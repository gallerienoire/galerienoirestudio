#!/usr/bin/env python3
"""
Stage 5: Art Director — Galerie Noire AI Pipeline
===================================================
Takes the interior designer's verified assessment and creates a creative brief
for artwork generation. Includes: mood, color palette, composition, scale,
subject matter, texture, materials, luxury influences.

The brief becomes the prompt for artwork generation — based solely on
verified observations, never invented details.
"""

import json, sys
from pathlib import Path


def load_design(design_path):
    with open(design_path) as f:
        return json.load(f)


def create_brief(design_path):
    """Create artwork creative brief from verified design assessment."""
    data = load_design(design_path)
    assessment = data.get("design_assessment", {})
    observations = assessment.get("observations", [])

    # Extract verified facts from observations
    colors = []
    brightness = None
    texture = None
    orientation = None

    for obs in observations:
        text = obs.get("observation", "").lower()
        if "color palette" in text:
            # Extract hex colors from text
            parts = text.split("#")
            for p in parts[1:]:
                hex_color = p.strip().split()[0] if p.strip() else ""
                if hex_color and len(hex_color) == 6:
                    colors.append(f"#{hex_color}")
        elif "brightness" in text:
            if "bright" in text:
                brightness = "bright"
            elif "moderate" in text:
                brightness = "moderate"
            else:
                brightness = "low"
        elif "texture" in text:
            if "minimal" in text:
                texture = "minimal"
            elif "moderate" in text:
                texture = "moderate"
            else:
                texture = "rich"
        elif "orientation" in text:
            if "horizontal" in text and "landscape" in text:
                orientation = "landscape"
            elif "vertical" in text:
                orientation = "portrait"
            else:
                orientation = "balanced"

    # Build artwork brief
    brief = {
        "artwork_brief": {
            "mood": _derive_mood(brightness, texture),
            "color_palette": {
                "source_colors": colors[:5],
                "direction": _derive_color_direction(colors)
            },
            "composition": {
                "orientation": orientation or "balanced",
                "scale_note": "Scale determined by room dimensions — see wall_space analysis in legacy pipeline"
            },
            "subject_matter": _derive_subject(brightness, texture),
            "style_influences": ["Contemporary abstraction — based on neutral color palette analysis"],
            "luxury_considerations": [
                "Premium paper or canvas substrate",
                "Archival-quality pigment inks",
                "Museum-grade framing recommended"
            ],
            "design_philosophy": (
                "This brief is generated from verified visual analysis only. "
                "Subject matter suggestions are compatible with the room's detected "
                "color character but are creative proposals, not confirmed requirements."
            )
        },
        "metadata": {
            "stage": 5,
            "engine": "art_director",
            "verified_observations_used": len(observations)
        }
    }

    return brief


def _derive_mood(brightness, texture):
    """Derive artwork mood from verified brightness and texture."""
    if brightness == "bright" and texture == "minimal":
        return "serene, airy, calm"
    elif brightness == "bright":
        return "energetic, vibrant, uplifting"
    elif brightness == "low":
        return "intimate, contemplative, moody"
    elif texture == "rich":
        return "dynamic, textured, layered"
    else:
        return "balanced, harmonious, refined"


def _derive_color_direction(colors):
    """Suggest color direction based on verified palette."""
    if not colors:
        return "neutral palette — warm grays, soft beiges, off-whites"
    return f"complement existing palette — {', '.join(colors[:3])}"


def _derive_subject(brightness, texture):
    """Suggest appropriate subject matter."""
    subjects = []
    if brightness == "bright":
        subjects.append("abstract landscapes, botanical studies, geometric compositions")
    elif brightness == "low":
        subjects.append("abstract nocturnes, tonal studies, textural compositions")
    else:
        subjects.append("abstract compositions, architectural studies, natural forms")

    if texture == "rich":
        subjects.append("layered mixed-media, impasto techniques")
    elif texture == "minimal":
        subjects.append("minimal line work, subtle gradients, monochromatic fields")

    return subjects


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python art_director.py <interior_designer_output.json> [--json]")
        sys.exit(1)
    result = create_brief(sys.argv[1])
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))
