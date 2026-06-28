#!/usr/bin/env python3
"""
Pipeline Orchestrator — Galerie Noire 8-Stage Verification System
==================================================================
Chains Stages 1–5: Vision Analyst → Skeptic → Consensus → Interior Designer → Art Director
Given a photo path, runs all stages sequentially and produces the final output.
"""

import json, os, subprocess, sys, tempfile
from pathlib import Path

PIPELINE_DIR = Path("/home/team/shared/ai-pipeline")
VENV_PYTHON = str(PIPELINE_DIR / "venv/bin/python")

SCRIPTS = {
    1: str(PIPELINE_DIR / "vision_analyst.py"),
    2: str(PIPELINE_DIR / "skeptic.py"),
    3: str(PIPELINE_DIR / "consensus.py"),
    4: str(PIPELINE_DIR / "interior_designer.py"),
    5: str(PIPELINE_DIR / "art_director.py"),
}

OUTPUT_DIR = PIPELINE_DIR / "output"


def run_stage(script, *args):
    """Run a stage script and return parsed JSON output."""
    cmd = [VENV_PYTHON, script] + list(args) + ["--json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Stage failed (exit {r.returncode}): {r.stderr[:300]}")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON parse error: {e}. stdout: {r.stdout[:200]}")


def run_pipeline(image_path, output_dir=None):
    """Run all 5 stages on an image. Saves intermediate outputs."""
    if output_dir is None:
        output_dir = OUTPUT_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    print(f"Galerie Noire — Verification Pipeline (Stages 1–5)")
    print(f"Input: {image_path}")
    print("=" * 60)

    # Stage 1: Vision Analyst
    print("[1/5] Vision Analyst: observing pixel-level facts...")
    s1 = run_stage(SCRIPTS[1], image_path)
    s1_path = output_dir / "stage1_vision.json"
    with open(s1_path, "w") as f:
        json.dump(s1, f, indent=2)
    print(f"       Saved to {s1_path}")

    # Stage 2: Skeptic
    print("[2/5] Skeptic: challenging every claim...")
    s2 = run_stage(SCRIPTS[2], image_path, str(s1_path))
    s2_path = output_dir / "stage2_skeptic.json"
    with open(s2_path, "w") as f:
        json.dump(s2, f, indent=2)
    print(f"       Saved to {s2_path}")

    # Stage 3: Consensus
    print("[3/5] Consensus Reviewer: building verified profile...")
    s3 = run_stage(SCRIPTS[3], image_path, str(s1_path), str(s2_path))
    s3_path = output_dir / "stage3_consensus.json"
    with open(s3_path, "w") as f:
        json.dump(s3, f, indent=2)
    print(f"       Saved to {s3_path}")

    # Stage 4: Interior Designer
    print("[4/5] Interior Designer: design from verified facts...")
    s4 = run_stage(SCRIPTS[4], str(s3_path))
    s4_path = output_dir / "stage4_interior_design.json"
    with open(s4_path, "w") as f:
        json.dump(s4, f, indent=2)
    print(f"       Saved to {s4_path}")

    # Stage 5: Art Director
    print("[5/5] Art Director: creating artwork brief...")
    s5 = run_stage(SCRIPTS[5], str(s4_path))
    s5_path = output_dir / "stage5_art_brief.json"
    with open(s5_path, "w") as f:
        json.dump(s5, f, indent=2)
    print(f"       Saved to {s5_path}")

    print("=" * 60)
    print("Pipeline complete! All 5 stages ran successfully.")
    print(f"Outputs in: {output_dir}")

    return {
        "stage1_vision": str(s1_path),
        "stage2_skeptic": str(s2_path),
        "stage3_consensus": str(s3_path),
        "stage4_design": str(s4_path),
        "stage5_art_brief": str(s5_path),
        "art_brief": s5
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("Usage: python pipeline_orchestrator.py <image_path> [--output-dir <dir>]")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = None
    if "--output-dir" in sys.argv:
        idx = sys.argv.index("--output-dir")
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]

    result = run_pipeline(image_path, output_dir)
    print(json.dumps(result, indent=2))
