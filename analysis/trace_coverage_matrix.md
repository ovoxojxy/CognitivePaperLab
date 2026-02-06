# Trace Coverage Matrix

Key decision variables and their observability: results vs traces vs neither.

| Decision Variable | In Results | In Traces | Neither |
|-------------------|------------|-----------|--------|
| format | ✓ (config) | ✗ | |
| order | ✓ (config) | ✗ | |
| normalize_keys | ✓ (config) | ✗ | |
| skip_validation | ✓ (config) | ✗ | |
| validate_config params | | ✓ (traces) | |
| validate_config outcome | ✓ (outputs) | ✓ (traces) | |
| rate_limit value (Turn 1) | | | ✓ (conversation only) |
| config status (Turn 2) | | ✓ (if logged) | |
| re-query decision | | ✓ (call sequence) | |

## Notes

- **format/order/normalize_keys/skip_validation**: Observable in run config, not in trace events. Changes to these produce output diffs that traces may not explain.
- **validate_config params**: Traced at decision point. Observable in traces.
- **rate_limit from Turn 1**: Conversation stream; not in results or traces unless explicitly logged.
- **re-query decision**: Inferred from tool call sequence in traces; no direct "did_requery" field.
