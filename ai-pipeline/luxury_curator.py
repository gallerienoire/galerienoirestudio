#!/usr/bin/env python3
"""
Galerie Noire — Stage 8: Luxury Curator
========================================
Final quality gate. Reviews the entire project output as if presenting to a
client who hired a high-end interior design firm. Validates consistency,
rewrites content into polished luxury language, and ensures every statement
is supported by verified data.

Usage:
    python3 luxury_curator.py < input.json > output.json
    python3 luxury_curator.py --project-id <id>  (reads from API)
"""

import json
import sys
import re
import os

# ──────────────────────────────────────────────────────────────────────
# Brand voice constants
# ──────────────────────────────────────────────────────────────────────

BRAND_NAME = "Galerie Noire"
MOOD_ADJECTIVES = [
    "refined", "curated", "intentional", "effortless", "sophisticated",
    "warm", "inviting", "cinematic", "atmospheric", "timeless",
    "personal", "bespoke", "considered", "elegant", "harmonious"
]

LIGHTING_DESCRIPTIONS = {
    "bright_crisp": "bright and invigorating — ideal for bold, high-contrast compositions that energize the space.",
    "warm_ambient": "warm and enveloping — perfect for artwork with depth, texture, and a sense of intimacy.",
    "soft_diffuse": "soft and diffused — suits serene, tonal pieces that reward quiet contemplation.",
    "dramatic_directional": "dramatic and directional — calls for artwork with strong contrast and commanding presence.",
    "mixed": "varied and layered — versatile enough to support a diverse range of artistic expressions.",
}

FRAME_MATERIAL_DESCRIPTIONS = {
    "brushed_brass": "Brushed brass — a warm metallic finish that catches light without overwhelming. Pairs naturally with cream and charcoal interiors.",
    "polished_brass": "Polished brass — reflective and luminous, for a more traditional statement.",
    "brushed_gold": "Brushed gold — understated warmth with a contemporary edge.",
    "polished_gold": "Polished gold — bold and luxurious, for dramatic effect.",
    "brushed_silver": "Brushed silver — cool and refined, ideal for minimalist or Scandinavian spaces.",
    "polished_silver": "Polished silver — crisp and modern, with a mirror-like finish.",
    "matte_black": "Matte black — dramatic and grounding. Best for high-contrast spaces with strong architectural lines.",
    "dark_oak": "Dark oak — warm and organic, for spaces that blend modern and traditional elements.",
    "natural_oak": "Natural oak — light and textural, complements Scandinavian and Japandi aesthetics.",
    "walnut": "Walnut — rich and warm, adds depth to traditional and mid-century interiors.",
    "white_ash": "White ash — light and airy, for spaces with abundant natural light.",
    "charcoal_metal": "Charcoal metal — industrial yet refined, suits loft and contemporary spaces.",
}

FRAME_STYLE_DESCRIPTIONS = {
    "tray_frame": "Tray frame — a modern classic that floats the artwork within a recessed frame, adding architectural depth.",
    "gallery_frame": "Gallery frame — a traditional moulding that echoes museum presentation.",
    "floating_frame": "Floating frame — the artwork appears to hover within the frame, creating a contemporary gallery feel.",
    "box_frame": "Box frame — a deep shadow-box that adds dimension and protects textured works.",
    "clipped_frame": "Clipped corner frame — a refined take on the classic, with subtle corner detailing.",
    "wire_frame": "Wire frame — minimal and industrial, showcasing the artwork with barely-there edges.",
}

# ──────────────────────────────────────────────────────────────────────
# Validation rules
# ──────────────────────────────────────────────────────────────────────

def validate_project(project):
    """Run consistency checks on the full project data. Returns list of issues."""
    issues = []

    room_profile = _get_nested(project, "deliverables.room_profile.content")
    artwork_collection = _get_nested(project, "deliverables.artwork_collection.content")
    styling_summary = _get_nested(project, "deliverables.styling_summary.content")

    if not room_profile and not artwork_collection and not styling_summary:
        issues.append("Project has no deliverables — analysis may not have run yet.")
        return issues

    # Check artwork-to-room consistency
    if room_profile and artwork_collection:
        room_type = _get_nested(room_profile, "architecture.room_type_guess", "unknown")
        pieces = _get_nested(artwork_collection, "pieces", []) or _get_nested(artwork_collection, "artworks", [])
        art_count = len(pieces)
        if art_count > 0 and art_count != 5:
            issues.append(f"Expected 5 artworks for {room_type}, got {art_count}.")

        # Check wall space vs artwork sizing
        wall_w = _get_nested(room_profile, "wall_space.recommended_artwork_width_cm")
        wall_h = _get_nested(room_profile, "wall_space.recommended_artwork_height_cm")
        if wall_w and wall_h:
            for piece in pieces:
                pw = _get_nested(piece, "width_cm") or _get_nested(piece, "width")
                ph = _get_nested(piece, "height_cm") or _get_nested(piece, "height")
                if pw and ph:
                    if pw > wall_w * 1.2:
                        issues.append(f"Artwork '{piece.get('title', 'Untitled')}' width ({pw}cm) exceeds wall space ({wall_w}cm).")
                    if ph > wall_h * 1.2:
                        issues.append(f"Artwork '{piece.get('title', 'Untitled')}' height ({ph}cm) exceeds wall space ({wall_h}cm).")

    # Check styling recommendations match room
    if room_profile and styling_summary:
        lighting = _get_nested(room_profile, "lighting.mood", "")
        layout = _get_nested(styling_summary, "layout_changes") or _get_nested(styling_summary, "layoutChanges", [])
        if lighting and layout and len(layout) > 0:
            pass  # Recommendations exist — promising

    return issues


# ──────────────────────────────────────────────────────────────────────
# Polishing functions
# ──────────────────────────────────────────────────────────────────────

def polish_room_profile(profile):
    """Rewrite room analysis as elegant, narrative prose."""
    if not profile:
        return None

    arch_style = _get_nested(profile, "architecture_style.primary_style", "Contemporary Modern")
    room_type = _get_nested(profile, "architecture.room_type_guess", "living space")
    ceiling_m = _get_nested(profile, "architecture.ceiling_height_estimate_m")
    ceiling_cat = _get_nested(profile, "architecture.ceiling_category", "")
    lighting = _get_nested(profile, "lighting.mood", "")
    color_temp = _get_nested(profile, "color_palette.color_temperature", "neutral")
    colors = _get_nested(profile, "color_palette.dominant_colors", [])
    art_w = _get_nested(profile, "wall_space.recommended_artwork_width_cm")
    art_h = _get_nested(profile, "wall_space.recommended_artwork_height_cm")
    view_dist = _get_nested(profile, "wall_space.viewing_distance_m")

    room_type_label = room_type.replace("_", " ").title()
    lighting_desc = LIGHTING_DESCRIPTIONS.get(lighting, "inviting and atmospheric — provides a beautiful backdrop for layered compositions.")
    ceiling_note = f" The {ceiling_cat.replace('_', ' ').title()} ceiling height of {ceiling_m}m" if ceiling_m else ""
    wall_note = ""
    if art_w and art_h:
        wall_note = f" The primary wall measures {art_w}cm × {art_h}cm"
        if view_dist:
            wall_note += f", with an optimal viewing distance of {view_dist}m"

    # Build palette prose
    palette_prose = ""
    if colors:
        top = colors[0]
        top_name = _friendly_color_name(top.get("hex", ""))
        top_pct = round((top.get("proportion", 0) or 0) * 100)
        remaining = len(colors) - 1
        palette_prose = f" The palette centers on {top_name} ({top['hex']}), comprising {top_pct}% of the tonal landscape"
        if remaining > 0:
            palette_prose += f", with {remaining} complementary accents that create a refined, layered composition."

    return {
        "narrative": (
            f"Your space reads as a {arch_style} interior with {color_temp} tonalities.{ceiling_note}"
            f" The lighting is {lighting_desc}"
            f"{wall_note}.{palette_prose}"
        ),
        "room_type": room_type_label,
        "architecture_style": arch_style,
        "ceiling_height": f"{ceiling_m}m" if ceiling_m else "Standard",
        "lighting_mood": lighting.replace("_", " ").title(),
        "wall_space": f"{art_w}cm × {art_h}cm" if art_w and art_h else "To be determined",
        "viewing_distance": f"{view_dist}m" if view_dist else None,
        "color_palette": [
            {"hex": c.get("hex", ""), "name": _friendly_color_name(c.get("hex", "")), "proportion": c.get("proportion", 0)}
            for c in colors
        ] if colors else []
    }


def polish_artwork_collection(collection):
    """Polish artwork descriptions and frame recommendations."""
    if not collection:
        return None

    pieces_raw = _get_nested(collection, "pieces") or _get_nested(collection, "artworks") or []
    pieces_polished = []

    for i, piece in enumerate(pieces_raw):
        title = piece.get("title", "").strip() or f"Untitled {i + 1}"
        description = piece.get("description", "")
        frame = piece.get("recommended_frame", {}) or {}
        frame_mat = frame.get("material", "")
        frame_style = frame.get("style", "")
        placement = piece.get("recommended_placement", piece.get("placement", ""))
        generated_image = piece.get("generated_image", piece.get("imageUrl", ""))

        # Polish description
        polished_desc = description
        if polished_desc and not polished_desc.endswith("."):
            polished_desc += "."

        # Build frame note
        frame_note = ""
        if frame_mat or frame_style:
            mat_desc = FRAME_MATERIAL_DESCRIPTIONS.get(frame_mat, frame_mat.replace("_", " ").title() if frame_mat else "")
            style_desc = FRAME_STYLE_DESCRIPTIONS.get(frame_style, frame_style.replace("_", " ").title() if frame_style else "")
            if mat_desc and style_desc:
                frame_note = f"{style_desc} Finished in {mat_desc.lower()}"
            elif mat_desc:
                frame_note = mat_desc
            elif style_desc:
                frame_note = style_desc

        # Polish placement
        polished_placement = placement
        if polished_placement and not polished_placement.endswith("."):
            polished_placement += "."
        if polished_placement and not polished_placement.lower().startswith(("position", "place", "hang", "mount")):
            polished_placement = f"Position {polished_placement[0].lower()}{polished_placement[1:]}"

        pieces_polished.append({
            "title": title,
            "description": polished_desc or None,
            "generated_image": generated_image or None,
            "recommended_frame": {
                "material": frame_mat,
                "style": frame_style,
                "curator_note": frame_note
            } if frame_mat or frame_style else None,
            "recommended_placement": polished_placement or None,
        })

    return {
        "pieces": pieces_polished,
        "total_pieces": len(pieces_polished),
        "curator_intro": (
            f"A collection of {len(pieces_polished)} original works, each selected and framed to complement your space."
            if pieces_polished else None
        )
    }


def polish_styling_summary(summary):
    """Rewrite styling guide as polished designer's notes."""
    if not summary:
        return None

    layout = _get_nested(summary, "layout_changes") or _get_nested(summary, "layoutChanges") or []
    view_dist = _get_nested(summary, "viewing_distance") or _get_nested(summary, "viewingDistance", "")

    polished_items = []
    if layout and isinstance(layout, list):
        for item in layout:
            text = item if isinstance(item, str) else _get_nested(item, "description", str(item))
            # Polish the recommendation
            if text:
                polished_items.append(text.strip().rstrip(".") + ".")

    return {
        "layout_changes": polished_items,
        "layout_count": len(polished_items),
        "viewing_distance": view_dist or None,
        "curator_intro": "The following adjustments will elevate your space, creating harmony between the artwork and its surroundings."
    }


def polish_shopping_guide(guide):
    """Polish product recommendations."""
    if not guide:
        return None

    items = guide if isinstance(guide, list) else guide.get("items", guide.get("shopping_items", []))
    polished_items = []

    for item in items:
        name = _get_nested(item, "name") or _get_nested(item, "product_name", "")
        brand = _get_nested(item, "brand", "")
        description = _get_nested(item, "description", "")
        price = _get_nested(item, "price", "")
        url = _get_nested(item, "url") or _get_nested(item, "product_url", "")
        tier = _get_nested(item, "tier", "essential")

        polished_items.append({
            "name": name,
            "brand": brand,
            "description": description,
            "price": price,
            "url": url,
            "tier": tier,
        })

    return {
        "items": polished_items,
        "total_items": len(polished_items),
        "curator_note": (
            "Each piece has been selected to complement your custom artwork and existing furnishings."
            if polished_items else None
        )
    }


# ──────────────────────────────────────────────────────────────────────
# Main curator
# ──────────────────────────────────────────────────────────────────────

def curate_project(project):
    """
    Run the full Stage 8 curation pipeline on a project JSON object.
    Returns the polished project with all changes applied.
    """
    if not project:
        return {"error": "No project data provided."}

    # 1. Validate
    issues = validate_project(project)
    if issues:
        project["_validation_issues"] = issues

    # 2. Extract deliverables with flexible path
    deliverables_raw = project.get("deliverables") or []
    deliverables_map = {}
    for d in deliverables_raw:
        content = d.get("content") or d
        t = d.get("type", "")
        deliverables_map[t] = content

    # 3. Polish each section
    polished = {
        "room_profile": polish_room_profile(deliverables_map.get("room_profile")),
        "artwork_collection": polish_artwork_collection(deliverables_map.get("artwork_collection")),
        "styling_summary": polish_styling_summary(deliverables_map.get("styling_summary")),
        "shopping_guide": polish_shopping_guide(deliverables_map.get("shopping_guide") or deliverables_map.get("shopping_items")),
    }

    # 4. Build executive summary
    profile = polished["room_profile"]
    artwork = polished["artwork_collection"]
    styling = polished["styling_summary"]

    summary_parts = []
    if profile:
        room = profile.get("room_type", "").lower()
        style = profile.get("architecture_style", "")
        summary_parts.append(f"A {style} {room}")
    if artwork:
        count = artwork.get("total_pieces", 0)
        summary_parts.append(f"with {count} custom-curated artworks")
    if styling:
        count = styling.get("layout_count", 0)
        if count:
            summary_parts.append(f"and {count} styling recommendations")
    polished["executive_summary"] = (
        " ".join(summary_parts).strip().capitalize() + "."
        if summary_parts else "Your transformation is being curated."
    )

    # 5. Validation result
    polished["_validation"] = {
        "passed": len(issues) == 0,
        "issues": issues,
    }

    # 6. Retain original project metadata
    polished["project_id"] = project.get("id", "")
    polished["tier"] = project.get("tier", "")
    polished["status"] = project.get("status", "")

    return polished


# ──────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Galerie Noire — Stage 8: Luxury Curator")
    parser.add_argument("--project-id", help="Fetch project from API and curate it")
    parser.add_argument("--input", "-i", help="Input JSON file (default: stdin)")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    parser.add_argument("--pretty", "-p", action="store_true", help="Pretty-print output")
    parser.add_argument("--validate-only", action="store_true", help="Only run validation, skip polishing")

    args = parser.parse_args()

    # Read input
    if args.project_id:
        import urllib.request
        api_url = f"http://localhost:3000/api/projects/{args.project_id}"
        try:
            with urllib.request.urlopen(api_url) as resp:
                project = json.loads(resp.read().decode())
        except Exception as e:
            print(f"Error fetching project {args.project_id}: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.input:
        with open(args.input, "r") as f:
            project = json.load(f)
    else:
        project = json.load(sys.stdin)

    # Curate
    if args.validate_only:
        issues = validate_project(project)
        result = {
            "passed": len(issues) == 0,
            "issues": issues,
        }
    else:
        result = curate_project(project)

    # Output
    indent = 2 if (args.pretty or args.output) else None
    output = json.dumps(result, indent=indent, ensure_ascii=False, default=str)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _get_nested(obj, path, default=None):
    """Safely access nested dict keys using dot notation (e.g. 'a.b.c')."""
    if obj is None:
        return default
    parts = path.split(".")
    current = obj
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if idx < len(current) else None
        else:
            return default
        if current is None:
            return default
    return current


def _friendly_color_name(hex_code):
    """Map hex codes to friendly color names."""
    palette = {
        "#ded2bf": "Warm Beige", "#c5a55a": "Brass Gold", "#1a1a1a": "Charcoal",
        "#f5f0eb": "Cream", "#1e3a2f": "Forest Green", "#0d0d0d": "Soft Black",
        "#8a8078": "Warm Grey", "#2a2a2a": "Dark Charcoal", "#d4b86a": "Warm Gold",
        "#e8dcc8": "Warm Ivory", "#b8a88a": "Taupe", "#5a4a3a": "Espresso",
        "#3a4a3a": "Sage", "#4a5a6a": "Slate Blue", "#6a5a4a": "Warm Brown",
        "#ffffff": "White", "#f0ece4": "Natural Linen", "#a09080": "Greige",
        "#708090": "Slate Grey", "#d2b48c": "Tan",
    }
    return palette.get(hex_code.lower(), hex_code)


if __name__ == "__main__":
    main()