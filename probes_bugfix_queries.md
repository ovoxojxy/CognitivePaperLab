# Probes and Bugfix Evaluation Queries

Queries to test LLM understanding of the analysis probes implementation and the trace emitter / normalize_output bugfixes. Answers require using Slack channel history (#cognitive-paper-code-base, #cognitive-foundations-for-reasoning-paper-extension), code in analysis/, and run artifacts in runs/.

---

## Query 1

**Question**: When the explainability diff was run on runs/20250205_perturb vs runs/20250205_perturb_no_explain, what was the judgment and why? What bug did the team discover that explained this result?

**Reference Answer**: Judgment was traces_do_not_explain. Outputs differed at query 0 (Brent vs Alex commit author) but traces were identical. Bug: trace_emitter.py silently skipped commit_author_selection due to an early return. Fix: removed that return.

**Expected Tool Calls**:
- Slack: Get channel history from #cognitive-paper-code-base for explainability diff discussion
- Read analysis/scripts/explainability_diff.py to understand the judgment logic
- Read analysis/trace_emitter.py (or git history) to see the fix
- Optionally run explainability_diff.py on the two run folders to reproduce

**Difficulty**: Medium

---

## Query 2

**Question**: What two field names in normalize_output.py should be coerced from string to int when the value is numeric? Why did the inconsistent coercion (before the fix) cause problems for the analysis?

**Reference Answer**: record_count and count. Before the fix only record_count was coerced, so runs with count as string vs int produced spurious diffs. Fix: added count to the coercion check.

**Expected Tool Calls**:
- Read analysis/normalize_output.py
- Slack: Get channel history about normalize_output and count coercion discussion

**Difficulty**: Easy-Medium
