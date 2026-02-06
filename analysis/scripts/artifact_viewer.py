#!/usr/bin/env python3
"""Thin wrapper: run artifact_viewer from scripts."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from analysis.artifact_viewer import main
if __name__ == "__main__":
    main()