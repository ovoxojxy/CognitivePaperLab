"""Write and read run manifests.

manifest.json contains: config, input_provenance, trace_schema_version, normalize_output_version.
"""

import json
from pathlib import Path

NORMALIZE_OUTPUT_VERSION = "1.0"
TRACE_SCHEMA_VERSION = "v1"  # trace_0.json, trace_3.json style


def write_manifest(run_path: Path, config: dict, input_provenance: str = "") -> None:
    """Write manifest.json for a run folder."""
    manifest = {
        "config": config,
        "input_provenance": input_provenance or str(run_path),
        # BUG: typo trace_schemaversion - should be trace_schema_version
        "trace_schemaversion": TRACE_SCHEMA_VERSION,
        "normalize_output_version": NORMALIZE_OUTPUT_VERSION,
    }
    with open(run_path / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


def read_manifest(run_path: Path) -> dict | None:
    """Read manifest.json. Returns None if missing."""
    p = run_path / "manifest.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)
