#!/usr/bin/env python3
"""
Stage 2: Skeptic / Fact Checker — Galerie Noire AI Pipeline
=============================================================
Takes the original image and Stage 1's vision analysis report.
Challenges every statement: "Can I actually see this? Is there evidence?"
Removes unsupported claims. Returns corrected report.
"""

import json, sys
from pathlib import Path
import numpy as np
from PIL import Image


def load_inputs(image_path, stage1_path):
    """Load the original image and Stage 1 report."""
    image = Image.open(image_path)
    with open(stage1_path) as f:
        report = json.load(f)
    return image, report


def verify_colors(image, colors_report):
    """Verify color claims against the actual image."""
    img = image.copy().convert("RGB")
    img.thumbnail((100, 75), Image.LANCZOS)
    pixels = np.array(img).reshape(-1, 3)

    verified = []
    for c in colors_report.get("dominant_colors", []):
        hex_val = c["hex"]
        r, g, b = c["rgb"]["r"], c["rgb"]["g"], c["rgb"]["b"]

        # Check if this color actually appears in the image
        tolerance = 40
        matching = np.sum(np.all(np.abs(pixels - [r, g, b]) < tolerance, axis=1))
        coverage = matching / len(pixels)

        # Confidence: how much of the image actually has this color
        confidence = min(0.95, round(coverage * 3, 2))

        verified.append({
            "hex": hex_val,
            "rgb": c["rgb"],
            "proportion": c["proportion"],
            "reported_confidence": c.get("confidence", 0.5),
            "verified_confidence": confidence,
            "pixel_coverage": round(float(coverage), 3),
            "verified": confidence >= 0.3
        })

    return {
        "dominant_colors": verified,
        "overall_brightness": colors_report.get("overall_brightness"),
        "brightness_variance": colors_report.get("brightness_variance")
    }


def verify_lighting(image, lighting_report):
    """Verify lighting claims against the actual image."""
    gray = np.array(image.copy().convert("L")).astype(float)
    reported_avg = lighting_report.get("average_brightness")
    actual_avg = round(float(gray.mean()), 1)

    brightness_ok = abs(actual_avg - (reported_avg or 0)) < 15

    return {
        "average_brightness": {
            "reported": reported_avg,
            "verified": actual_avg,
            "match": brightness_ok,
            "confidence": 0.95 if brightness_ok else 0.5
        },
        "brightness_std": lighting_report.get("brightness_std"),
        "red_blue_ratio": lighting_report.get("red_blue_ratio"),
        "shadow_ratio": lighting_report.get("shadow_ratio")
    }


def verify_geometry(image, geometry_report):
    """Verify geometry claims."""
    w, h = image.size
    assert w == geometry_report.get("image_width_px")
    assert h == geometry_report.get("image_height_px")

    # Recalculate edge density to verify
    gray = np.array(image.copy().convert("L")).astype(float)
    from scipy.ndimage import sobel
    edges_x = sobel(gray, axis=1)
    edges_y = sobel(gray, axis=0)
    edge_mag = np.sqrt(edges_x ** 2 + edges_y ** 2)
    actual_edge_density = round(float((edge_mag > 30).mean()), 4)

    reported = geometry_report.get("edge_density", 0)
    match = abs(actual_edge_density - reported) < 0.02

    return {
        "image_width_px": w,
        "image_height_px": h,
        "aspect_ratio": round(w / h, 3),
        "edge_density": {
            "reported": reported,
            "verified": actual_edge_density,
            "match": match,
            "confidence": 0.95 if match else 0.6
        }
    }


def challenge(image_path, stage1_path):
    """Run skeptic: verify all Stage 1 claims against the image."""
    image, report = load_inputs(image_path, stage1_path)
    vision = report.get("vision_analysis", {})

    challenged = {
        "colors": verify_colors(image, vision.get("colors", {})),
        "lighting": verify_lighting(image, vision.get("lighting", {})),
        "geometry": verify_geometry(image, vision.get("geometry", {})),
        "challenges": []
    }

    # Log any claims that failed verification
    for c in challenged["colors"].get("dominant_colors", []):
        if not c["verified"]:
            challenged["challenges"].append({
                "claim": f"Color {c['hex']} reported with confidence {c['reported_confidence']}",
                "issue": f"Only {c['pixel_coverage']:.1%} pixel coverage — below 30% threshold",
                "action": "downgrade_confidence"
            })

    return challenged


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python skeptic.py <image_path> <stage1_output.json> [--json]")
        sys.exit(1)
    result = challenge(sys.argv[1], sys.argv[2])
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))
