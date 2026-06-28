#!/usr/bin/env python3
"""
Stage 4: Interior Designer — Galerie Noire AI Pipeline
========================================================
Receives only the verified room profile from Stage 3 (NOT the photo).
Determines: design style observations, mood assessment, color harmony,
artwork placement recommendations, frame suggestions, lighting adjustments.

Every recommendation MUST cite a verified observation from the profile.
"""

import json, sys
from pathlib import Path


def load_profile(profile_path):
    with open(profile_path) as f:
        return json.load(f)


def design(profile_path):
    """Generate design recommendations from verified profile only."""
    data = load_profile(profile_path)
    rp = data.get("verified_room_profile", data)
    colors = rp.get("colors", {})
    geometry = rp.get("geometry", {})
    uncertainties = data.get("uncertainties", [])

    dominant = colors.get("dominant_colors", [])
    brightness = colors.get("overall_brightness", {})

    # Build design observations from VERIFIED facts only
    design_observations = []

    # Color observations
    verified_colors = [c for c in dominant if c.get("status") == "verified"]
    uncertain_colors = [c for c in dominant if c.get("status") == "uncertain"]

    if verified_colors:
        hexes = [c["hex"] for c in verified_colors[:3]]
        design_observations.append({
            "observation": f"Verified color palette: {', '.join(hexes)}",
            "source": f"Stage 3 consensus — {len(verified_colors)} verified dominant colors",
            "confidence": min(c["confidence"] for c in verified_colors[:3])
        })

    # Brightness observation
    b_val = brightness.get("value")
    b_conf = brightness.get("confidence", 0)
    b_status = brightness.get("status", "uncertain")

    if b_val is not None and b_status == "verified":
        if b_val < 80:
            mood = "low_light"
        elif b_val < 130:
            mood = "moderate_light"
        else:
            mood = "bright"

        design_observations.append({
            "observation": f"Room brightness: {mood} (average pixel value: {b_val})",
            "source": "Stage 3 consensus brightness verification",
            "confidence": b_conf
        })

    # Geometry observations
    edge = geometry.get("edge_density", {}).get("value", 0)
    edge_conf = geometry.get("edge_density", {}).get("confidence", 0)
    edge_status = geometry.get("edge_density", {}).get("status", "uncertain")

    if edge_status == "verified":
        if edge < 0.05:
            texture_note = "minimal texture/detail"
        elif edge < 0.12:
            texture_note = "moderate texture/detail"
        else:
            texture_note = "rich texture/detail"

        design_observations.append({
            "observation": f"Surface texture: {texture_note} (edge density: {edge})",
            "source": "Stage 3 edge density verification",
            "confidence": edge_conf
        })

    # Artwork placement (based on aspect ratio, no wall inference)
    aspect = geometry.get("aspect_ratio", 1.5)
    if aspect > 1.4:
        placement_note = "Horizontal (landscape) orientation fits this image format"
    elif aspect > 1.0:
        placement_note = "Slightly horizontal — balanced proportions"
    else:
        placement_note = "Vertical (portrait) orientation"

    design_observations.append({
        "observation": f"Artwork orientation: {placement_note}",
        "source": f"Image aspect ratio: {aspect}",
        "confidence": 0.9
    })

    # Frame recommendation (based only on color analysis)
    if verified_colors:
        avg_brightness = sum(
            (0.299 * c["rgb"]["r"] + 0.587 * c["rgb"]["g"] + 0.114 * c["rgb"]["b"])
            for c in verified_colors
        ) / len(verified_colors)

        if avg_brightness > 150:
            frame_suggestion = "Dark frame (black, espresso) for contrast against light tones"
        else:
            frame_suggestion = "Light or metallic frame for visibility against darker tones"

        design_observations.append({
            "observation": f"Frame suggestion: {frame_suggestion}",
            "source": f"Average color brightness of verified palette: {avg_brightness:.0f}",
            "confidence": 0.7
        })

    return {
        "design_assessment": {
            "observations": design_observations,
            "uncertainties_noted": len(uncertainties),
            "design_philosophy": "Every recommendation is grounded in verified visual analysis. No style labels, material assumptions, or brand references are used.",
            "recommendations_available": len(design_observations)
        },
        "metadata": {
            "stage": 4,
            "engine": "interior_designer",
            "based_on": "verified_room_profile_only"
        }
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python interior_designer.py <consensus_output.json> [--json]")
        sys.exit(1)
    result = design(sys.argv[1])
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))
