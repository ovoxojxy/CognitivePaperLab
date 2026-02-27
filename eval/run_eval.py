#!/usr/bin/env python3
"""
Eval runner: reads question bank, selects subset, resolves artifact refs,
produces eval bundle at eval_bundles/<timestamp>_<name>/.
"""

import argparse
import json
import random
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load_question_bank(path: Path) -> list[dict]:
    """Load question bank from JSONL file."""
    questions = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            questions.append(json.loads(line))
    return questions


def resolve_artifacts(repo_root: Path, questions: list[dict]) -> dict[str, list[Path]]:
    """Resolve artifact paths for each question. Returns question_id -> [resolved paths]."""
    resolved = {}
    for q in questions:
        aid = q.get("id", "")
        artifact = q.get("artifact", "")
        paths = []
        # Resolve run folders
        if artifact.startswith("runs/"):
            parts = artifact.split("/")
            run_name = parts[1] if len(parts) > 1 else ""
            run_dir = repo_root / "runs" / run_name
            if run_dir.exists():
                if len(parts) == 2:  # runs/20250204_surface
                    paths.append(run_dir)
                else:  # runs/20250204_surface/manifest.json or traces/
                    subpath = run_dir / "/".join(parts[2:])
                    if subpath.exists():
                        paths.append(subpath)
                    else:
                        paths.append(run_dir)
        elif "explainability_report" in artifact:
            # Check for report in known locations
            for cand in [
                repo_root / "runs" / "20250205_perturb" / "explainability_report.json",
                repo_root / "runs" / "20250205_perturb_no_explain" / "explainability_report.json",
                repo_root / "analysis" / "explainability_report.json",
            ]:
                if cand.exists():
                    paths.append(cand)
                    break
            if not paths:
                # Check eval_bundles for pre-computed reports
                eb = repo_root / "eval_bundles"
                if eb.exists():
                    for bundle_dir in sorted(eb.iterdir(), reverse=True):
                        rep = bundle_dir / "artifacts" / "explainability_report.json"
                        if rep.exists():
                            paths.append(rep)
                            break
        elif "manifest" in artifact or "config" in artifact:
            for run_dir in (repo_root / "runs").iterdir():
                if run_dir.is_dir():
                    m = run_dir / "manifest.json" if "manifest" in artifact else run_dir / "config.json"
                    if m.exists():
                        paths.append(m)
        elif "list_runs" in artifact or "artifact_viewer" in artifact or "run_manifest" in artifact:
            script = repo_root / "analysis" / "scripts" / ("list_runs.py" if "list_runs" in artifact else "artifact_viewer.py")
            if not script.exists() and "run_manifest" in artifact:
                script = repo_root / "analysis" / "run_manifest.py"
            if script.exists():
                paths.append(script)
        resolved[aid] = paths
    return resolved


def ensure_explainability_report(repo_root: Path) -> Path | None:
    """Generate explainability_report.json if missing. Returns path or None."""
    run_a = repo_root / "runs" / "20250205_perturb"
    run_b = repo_root / "runs" / "20250205_perturb_no_explain"
    if not run_a.exists() or not run_b.exists():
        return None
    report_path = run_a / "explainability_report.json"
    if report_path.exists():
        return report_path
    script = repo_root / "analysis" / "scripts" / "explainability_diff.py"
    if not script.exists():
        return None
    try:
        subprocess.run(
            [sys.executable, str(script), str(run_a), str(run_b), "--out", str(run_a)],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
        if report_path.exists():
            return report_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def create_bundle(
    repo_root: Path,
    questions: list[dict],
    name: str,
    out_dir: Path,
    copy_artifacts: bool = True,
    generate_report: bool = True,
) -> Path:
    """Create eval bundle folder with bundle.json, artifacts, instructions.txt."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_name = f"{timestamp}_{name}"
    bundle_dir = out_dir / bundle_name
    bundle_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = bundle_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    # Generate explainability_report if any question needs it
    needs_report = any("explainability_report" in q.get("artifact", "") for q in questions)
    if needs_report and generate_report:
        ensure_explainability_report(repo_root)

    resolved = resolve_artifacts(repo_root, questions)
    artifact_paths = set()
    for paths in resolved.values():
        for p in paths:
            if p.exists():
                artifact_paths.add(p)

    # Copy or symlink artifacts
    for src in artifact_paths:
        try:
            rel = src.relative_to(repo_root)
        except ValueError:
            rel = Path(src.name)
        dst = artifacts_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if copy_artifacts:
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
        else:
            # Store relative path only (reference)
            pass

    bundle = {
        "name": bundle_name,
        "created": datetime.now().isoformat(),
        "questions": questions,
        "resolved_artifacts": {qid: [str(p) for p in paths] for qid, paths in resolved.items()},
        "constraints": {
            "allowed_evidence": "artifacts in bundle only; no code inspection unless explicitly in artifact list",
            "underdetermined_expected": "say 'cannot infer from artifacts' for UNDERDETERMINED questions",
        },
    }

    with open(bundle_dir / "bundle.json", "w") as f:
        json.dump(bundle, f, indent=2)

    instructions = """Evidence allowed:
- Artifacts in the artifacts/ folder (run outputs, manifests, configs, traces, explainability_report)
- Do NOT use code as evidence unless the artifact explicitly includes script output (e.g. list_runs, artifact_viewer)

For questions marked underdetermined: answer "cannot infer from artifacts" or equivalent.

Cite artifact paths when giving answers.
"""

    with open(bundle_dir / "instructions.txt", "w") as f:
        f.write(instructions)

    # Write artifact paths manifest for reference
    with open(bundle_dir / "artifact_paths.json", "w") as f:
        json.dump(sorted(str(p) for p in artifact_paths), f, indent=2)

    return bundle_dir


def main():
    parser = argparse.ArgumentParser(description="Create eval bundle from question bank")
    parser.add_argument("--question-bank", "-q", default="eval/question_bank.jsonl", help="Path to question bank JSONL")
    parser.add_argument("--repo-root", "-r", default=".", help="Repo root (CognitivePaperLab)")
    parser.add_argument("--tag", "-t", help="Filter questions by tag")
    parser.add_argument("--subset", "-n", type=int, help="Random subset size")
    parser.add_argument("--ids", help="Comma-separated question IDs")
    parser.add_argument("--name", "-N", default="default", help="Bundle name suffix")
    parser.add_argument("--out-dir", "-o", default="eval_bundles", help="Output directory for bundles")
    parser.add_argument("--no-copy", action="store_true", help="Don't copy artifacts, store paths only")
    parser.add_argument("--no-generate-report", action="store_true", help="Don't auto-generate explainability_report")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    bank_path = repo_root / args.question_bank if not Path(args.question_bank).is_absolute() else Path(args.question_bank)
    if not bank_path.exists():
        print(f"Question bank not found: {bank_path}", file=sys.stderr)
        sys.exit(1)

    questions = load_question_bank(bank_path)

    if args.ids:
        ids = {i.strip() for i in args.ids.split(",")}
        questions = [q for q in questions if q.get("id") in ids]
    if args.tag:
        questions = [q for q in questions if args.tag in q.get("tags", [])]
    if args.subset and len(questions) > args.subset:
        questions = random.sample(questions, args.subset)

    out_dir = repo_root / args.out_dir
    bundle_dir = create_bundle(
        repo_root,
        questions,
        args.name,
        out_dir,
        copy_artifacts=not args.no_copy,
        generate_report=not args.no_generate_report,
    )
    print(f"Created {bundle_dir}", file=sys.stderr)
    print(str(bundle_dir))


if __name__ == "__main__":
    main()
