#!/usr/bin/env python3
"""
Score model answers against eval bundle.
Outputs score.json with correctness, underdetermined handling,
grounding compliance, overconfident penalty, and error categories.
"""

import argparse
import json
import re
import sys
from pathlib import Path


ERROR_CATEGORIES = [
    "missing_evidence_hallucination",
    "wrong_artifact_retrieval",
    "wrong_inference_from_correct_artifact",
    "normalization_confusion",
    "uncertainty_calibration_error",
]


def normalize_answer(s: str) -> str:
    """Normalize answer for comparison."""
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _normalize_for_match(s: str) -> str:
    """Additional normalization for flexible matching (punctuation variants)."""
    s = re.sub(r"[\s:\(\)\,\;]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def answers_match(expected: str, actual: str) -> bool:
    """Check if actual matches expected. Uses word-boundary for short answers (yes/no)."""
    ne = normalize_answer(expected)
    na = normalize_answer(actual)
    if ne == na:
        return True
    if not ne or not na:
        return False
    # For short answers like yes/no, require word boundary to avoid "no" in "normalization"
    if len(ne) <= 4 and ne in ("yes", "no", "true", "false"):
        return bool(re.search(rf"\b{re.escape(ne)}\b", na))
    # For longer answers, allow substring; also try punctuation-normalized
    if ne in na or na in ne:
        return True
    ne2 = _normalize_for_match(ne)
    na2 = _normalize_for_match(na)
    return ne2 in na2 or na2 in ne2


def check_underdetermined_response(text: str) -> bool:
    """Check if response indicates 'cannot infer' or equivalent."""
    if not text:
        return False
    t = normalize_answer(text)
    patterns = [
        r"cannot infer",
        r"can't infer",
        r"cannot determine",
        r"can't determine",
        r"not inferable",
        r"underdetermined",
        r"insufficient.*evidence",
        r"no.*evidence",
        r"unknown",
        r"unclear from artifacts",
    ]
    return any(re.search(p, t) for p in patterns)


def check_grounding(text: str, allowed_artifacts: list[str]) -> bool:
    """Check if response cites allowed artifacts (paths, manifest, trace, etc.)."""
    if not text or not allowed_artifacts:
        return True  # No constraint
    t = text.lower()
    refs = ["manifest", "trace", "outputs", "config", "explainability", "runs/", "normalization_note", "report"]
    return any(ref in t for ref in refs)


def check_overconfident_mechanistic(text: str, code_not_allowed: bool) -> bool:
    """Check for overconfident mechanistic claims when code not allowed."""
    if not code_not_allowed:
        return False
    t = text.lower()
    # Claims about internal logic, implementation details
    overconfident = [
        "the code does",
        "the function",
        "the implementation",
        "line [0-9]+",
        "def ",
        "because the model",
    ]
    return any(re.search(p, t) for p in overconfident)


def classify_error(
    question: dict,
    expected: str,
    actual: str,
    is_underdetermined: bool,
    said_cannot_infer: bool,
) -> str | None:
    """Classify error category."""
    if is_underdetermined:
        if not said_cannot_infer and actual:
            return "uncertainty_calibration_error"
        return None
    # Inferable but wrong
    if not actual or "cannot infer" in normalize_answer(actual):
        return "missing_evidence_hallucination"
    if "normaliz" in (expected + actual).lower() or "raw" in (expected + actual).lower() or "coerc" in (expected + actual).lower():
        return "normalization_confusion"
    # Could be wrong retrieval or wrong inference - heuristic
    return "wrong_inference_from_correct_artifact"


def score_answer(
    question: dict,
    model_answer: str,
    code_allowed: bool = False,
) -> dict:
    """Score a single answer."""
    qid = question.get("id", "")
    expected = question.get("expected_answer", "")
    expected_label = question.get("expected_label", "INFERABLE")
    is_underdetermined = question.get("underdetermined", False) or expected_label == "UNDERDETERMINED"

    result = {
        "question_id": qid,
        "correctness": False,
        "underdetermined_handling": None,
        "grounding_compliant": True,
        "overconfident_penalty": 0,
        "error_category": None,
    }

    said_cannot_infer = check_underdetermined_response(model_answer)

    if is_underdetermined:
        result["underdetermined_handling"] = said_cannot_infer
        result["correctness"] = said_cannot_infer
    else:
        result["correctness"] = answers_match(expected, model_answer)
        if not result["correctness"]:
            result["error_category"] = classify_error(
                question, expected, model_answer, is_underdetermined, said_cannot_infer
            )

    result["grounding_compliant"] = check_grounding(model_answer, question.get("evidence_pointers", []))
    if check_overconfident_mechanistic(model_answer, not code_allowed):
        result["overconfident_penalty"] = 1

    return result


def load_answers(path: Path) -> dict[str, str]:
    """Load model answers. Expects JSON { "q1": "answer", ... } or JSONL with id/answer."""
    answers = {}
    with open(path) as f:
        content = f.read().strip()
    if content.startswith("{"):
        data = json.loads(content)
        for k, v in data.items():
            answers[k] = str(v) if v is not None else ""
    else:
        for line in content.splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            qid = obj.get("id") or obj.get("question_id")
            ans = obj.get("answer") or obj.get("model_answer") or obj.get("response")
            if qid:
                answers[qid] = str(ans) if ans is not None else ""
    return answers


def main():
    parser = argparse.ArgumentParser(description="Score model answers against eval bundle")
    parser.add_argument("bundle_dir", help="Path to eval bundle directory")
    parser.add_argument("answers_file", help="Path to model answers (JSON or JSONL)")
    parser.add_argument("-o", "--output", default="score.json", help="Output score file")
    parser.add_argument("--code-allowed", action="store_true", help="Code evidence is allowed")
    args = parser.parse_args()

    bundle_dir = Path(args.bundle_dir)
    bundle_path = bundle_dir / "bundle.json"
    if not bundle_path.exists():
        print(f"Bundle not found: {bundle_path}", file=sys.stderr)
        sys.exit(1)

    with open(bundle_path) as f:
        bundle = json.load(f)

    answers_path = Path(args.answers_file)
    if not answers_path.exists():
        print(f"Answers file not found: {answers_path}", file=sys.stderr)
        sys.exit(1)

    model_answers = load_answers(answers_path)
    questions = {q["id"]: q for q in bundle["questions"]}

    results = []
    for q in bundle["questions"]:
        qid = q["id"]
        ans = model_answers.get(qid, "")
        results.append(score_answer(q, ans, code_allowed=args.code_allowed))

    correct = sum(1 for r in results if r["correctness"])
    underdetermined_ok = sum(
        1 for r in results
        if r["underdetermined_handling"] is True
    )
    grounding_ok = sum(1 for r in results if r["grounding_compliant"])
    overconfident_total = sum(r["overconfident_penalty"] for r in results)
    error_counts = {}
    for r in results:
        ec = r.get("error_category")
        if ec:
            error_counts[ec] = error_counts.get(ec, 0) + 1

    score = {
        "bundle": bundle_dir.name,
        "answers_file": str(answers_path),
        "summary": {
            "total": len(results),
            "correct": correct,
            "correctness_rate": correct / len(results) if results else 0,
            "underdetermined_handled": underdetermined_ok,
            "grounding_compliant": grounding_ok,
            "overconfident_penalties": overconfident_total,
        },
        "per_question": results,
        "error_categories": error_counts,
    }

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = bundle_dir / out_path
    with open(out_path, "w") as f:
        json.dump(score, f, indent=2)

    print(f"Wrote {out_path}", file=sys.stderr)
    print(f"Correct: {correct}/{len(results)}", file=sys.stderr)
    print(json.dumps(score, indent=2))


if __name__ == "__main__":
    main()
