#!/usr/bin/env python3
"""Scan runs/ and print a table from manifests."""

import json
import sys
from pathlib import Path

# Add project root for analysis imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from analysis.run_manifest import read_manifest


def main():
    runs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs")
    if not runs_dir.exists():
        print("runs/ not found")
        sys.exit(1)

    rows = []
    for d in sorted(runs_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        m = read_manifest(d)
        if m:
            cfg = m.get("config", {})
            # Backwards compat: accept trace_schemaversion (typo) from old manifests
            trace_ver = m.get("trace_schema_version") or m.get("trace_schemaversion", "unknown")
            rows.append({
                "run": d.name,
                "format": cfg.get("format", "-"),
                "order": cfg.get("order", "-"),
                "trace_schema": trace_ver,
                "norm_version": m.get("normalize_output_version", "unknown"),
                "provenance": (m.get("input_provenance", "") or "-")[:40],
            })
        else:
            rows.append({
                "run": d.name,
                "format": "-",
                "order": "-",
                "trace_schema": "no manifest",
                "norm_version": "-",
                "provenance": "-",
            })

    if not rows:
        print("No runs found")
        return

    # Print table
    w_run = max(8, max(len(r["run"]) for r in rows))
    w_format = max(6, max(len(str(r["format"])) for r in rows))
    w_order = max(5, max(len(str(r["order"])) for r in rows))
    w_ts = max(10, max(len(str(r["trace_schema"])) for r in rows))
    w_norm = max(6, max(len(str(r["norm_version"])) for r in rows))

    fmt = f"{{run:<{w_run}}} {{format:<{w_format}}} {{order:<{w_order}}} {{trace_schema:<{w_ts}}} {{norm_version:<{w_norm}}} provenance"
    print(fmt.format(run="run", format="format", order="order", trace_schema="trace_ver", norm_version="norm_ver"))
    print("-" * (w_run + w_format + w_order + w_ts + w_norm + 50))
    for r in rows:
        print(fmt.format(**r) + " " + r["provenance"])
