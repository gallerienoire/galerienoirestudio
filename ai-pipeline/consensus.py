#!/usr/bin/env python3
"""
Stage 3: Consensus Reviewer — Galerie Noire AI Pipeline
=========================================================
Compares the original image + Stage 1 (Vision Analyst) + Stage 2 (Skeptic).
Creates the final verified room profile.
Disagreements between agents are marked as "uncertain".
This is the single source of truth for downstream stages.
"""

import json, sys
from pathlib import Path
import numpy as np
from PIL import Image


def load_inputs(image_path, stage1_path, stage2_path):
    image = Image.open(image_path)
    with open(stage1_path) as f:
        s1 = json.load(f)
    with open(stage2_path) as f:
        s2 = json.load(f)
    return image, s1, s2


def build_consensus(image, s1, s2):
    """Build consensus by comparing Stage 1 and Stage 2 findings."""
    v1 = s1.get("vision_analysis", {})
    v2 = s2

    # ─── Colors ───────────────────────────────────────────────────────────
    colors_s1 = v1.get("colors", {}).get("dominant_colors", [])
    colors_s2 = v2.get("colors", {}).get("dominant_colors", [])

    consensus_colors = []
    for c1 in colors_s1:
        hex_val = c1["hex"]
        # Find matching color in skeptic output
        c2 = next((c for c in colors_s2 if c["hex"] == hex_val), None)
        if c2:
            # Average the confidences, but use skeptic's verification
            final_conf = min(c1.get("confidence", 0.5), c2.get("verified_confidence", 0.5))
            status = "verified" if c2.get("verified", False) else "uncertain"
        else:
            final_conf = c1.get("confidence", 0.5) * 0.5  # Penalize unverified
            status = "uncertain"

        consensus_colors.append({
            "hex": hex_val,
            "rgb": c1["rgb"],
            "proportion": c1.get("proportion", 0),
            "confidence": round(final_conf, 2),
            "status": status
        })

    # ─── Brightness ───────────────────────────────────────────────────────
    brightness_s1 = v1.get("colors", {}).get("overall_brightness", 0)
    brightness_s2 = v2.get("lighting", {}).get("average_brightness", {})

    if isinstance(brightness_s2, dict):
        b_verified = brightness_s2.get("verified", brightness_s1)
        b_match = brightness_s2.get("match", True)
    else:
        b_verified = brightness_s1
        b_match = True

    brightness_conf = 0.9 if b_match else 0.5

    # ─── Geometry ─────────────────────────────────────────────────────────
    geo_s1 = v1.get("geometry", {})
    geo_s2 = v2.get("geometry", {})

    edge_s2 = geo_s2.get("edge_density", {})
    if isinstance(edge_s2, dict):
        edge_verified = edge_s2.get("verified", geo_s1.get("edge_density", 0))
        edge_match = edge_s2.get("match", True)
    else:
        edge_verified = geo_s1.get("edge_density", 0)
        edge_match = True

    return {
        "verified_room_profile": {
            "colors": {
                "dominant_colors": consensus_colors,
                "overall_brightness": {
                    "value": brightness_verified,
                    "confidence": brightness_conf,
                    "status": "verified" if brightness_conf >= 0.7 else "uncertain"
                }
            },
            "geometry": {
                "image_width_px": geo_s1.get("image_width_px"),
                "image_height_px": geo_s1.get("image_height_px"),
                "aspect_ratio": geo_s1.get("aspect_ratio"),
                "edge_density": {
                    "value": edge_verified,
                    "confidence": 0.9 if edge_match else 0.5,
                    "status": "verified" if edge_match else "uncertain"
                }
            }
        },
        "uncertainties": [],
        "metadata": {
            "stage": 3,
            "engine": "consensus_reviewer",
            "status": "verified_profile"
        }
    }


def consensus(image_path, stage1_path, stage2_path):
    image, s1, s2 = load_inputs(image_path, stage1_path, stage2_path)
    result = build_consensus(image, s1, s2)

    # Collect all uncertainties
    colors = result["verified_room_profile"]["colors"]["dominant_colors"]
    for c in colors:
        if c["status"] == "uncertain":
            result["uncertainties"].append({
                "item": f"color_{c['hex']}",
                "reason": f"Confidence {c['confidence']} below verification threshold"
            })

    return result


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python consensus.py <image_path> <stage1.json> <stage2.json> [--json]")
        sys.exit(1)
    result = consensus(sys.argv[1], sys.argv[2], sys.argv[3])
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))
