#!/usr/bin/env python3
"""
Styling Guide & Shopping Guide — Galerie Noire AI Pipeline (Step 3 & 4)
=======================================================================
Takes the room profile JSON from Step 1 and generates:

Step 3 — Styling Guide:
- Concrete layout change recommendations (move furniture, swap decor)
- Picture lighting and frame finish recommendations
- Specific, actionable instructions with measurements

Step 4 — Shopping Guide:
- Multi-tier recommendations (Luxury / Premium / Budget)
- Real retailer sources (Restoration Hardware, Design Within Reach, CB2, etc.)
- Furniture, lighting, rugs, accessories, and wall finishes
"""

import json
import math
import os
import sys
from pathlib import Path


# ─── Room Context Extraction ──────────────────────────────────────────────────

def load_room_profile(profile_path):
    """Load a room profile JSON file produced by Step 1."""
    with open(profile_path, 'r') as f:
        return json.load(f)


def extract_context(profile):
    """Extract key room characteristics for styling decisions."""
    rp = profile["room_profile"]
    
    colors = rp["color_palette"]["dominant_colors"]
    primary_hex = colors[0]["hex"] if len(colors) > 0 else "#DED2BF"
    accent_hex = colors[1]["hex"] if len(colors) > 1 else "#C5A55A"
    
    color_temp = rp["color_palette"]["color_temperature"]
    vibrancy = rp["color_palette"]["vibrancy"]
    
    lighting = rp["lighting"]
    brightness = lighting["brightness_level"]
    mood = lighting["mood"]
    color_temp_desc = lighting["color_temperature"]
    shadow = lighting["shadow_severity"]
    evenness = lighting["lighting_evenness"]
    
    arch = rp["architecture"]
    room_type = arch["room_type_guess"].replace("_", " ")
    ceiling_m = arch["ceiling_height_estimate_m"]
    ceiling_cat = arch["ceiling_category"]
    
    style = rp["architecture_style"]
    arch_style = style["primary_style"]
    
    furniture = rp["furniture"]
    layout = furniture["layout_style"]
    coverage = furniture["furniture_coverage"]
    items_count = furniture["items_detected_count"]
    surface = furniture["furniture_surface"]
    
    walls = rp["wall_space"]
    art_w = walls["recommended_artwork_width_cm"]
    art_h = walls["recommended_artwork_height_cm"]
    
    viewing = rp["viewing_distance"]
    view_dist = viewing["optimal_viewing_distance_m"]
    
    return {
        "primary_color": primary_hex,
        "accent_color": accent_hex,
        "color_temperature": color_temp,
        "vibrancy": vibrancy,
        "lighting_mood": mood,
        "lighting_brightness": brightness,
        "lighting_temp": color_temp_desc,
        "shadow_severity": shadow,
        "lighting_evenness": evenness,
        "room_type": room_type,
        "ceiling_height_m": ceiling_m,
        "ceiling_category": ceiling_cat,
        "architecture_style": arch_style,
        "furniture_layout": layout,
        "furniture_coverage": coverage,
        "furniture_count": items_count,
        "furniture_surface": surface,
        "artwork_width_cm": art_w,
        "artwork_height_cm": art_h,
        "viewing_distance_m": view_dist,
    }


# ─── Step 3: Styling Guide ────────────────────────────────────────────────────

def generate_layout_changes(ctx):
    """
    Generate specific, measurable layout change recommendations.
    Each recommendation includes: what to change, by how much, direction, and rationale.
    """
    layout = ctx["furniture_layout"]
    coverage = ctx["furniture_coverage"]
    items = ctx["furniture_count"]
    room = ctx["room_type"]
    mood = ctx["lighting_mood"]
    brightness = ctx["lighting_brightness"]
    shadow = ctx["shadow_severity"]
    ceiling = ctx["ceiling_height_m"]
    evenness = ctx["lighting_evenness"]
    arch_style = ctx["architecture_style"]
    surface = ctx["furniture_surface"]
    
    changes = []
    
    # 1. Sofa/Seating adjustment
    if coverage < 0.35:
        changes.append({
            "action": "Bring seating forward",
            "detail": f"Move the primary seating 15-20 cm (6-8 inches) closer to the focal wall. This reduces the viewing distance to {max(2.5, ctx['viewing_distance_m'] - 1.0):.1f}m, creating a more intimate conversation area.",
            "rationale": f"The current furniture coverage ({coverage:.0%}) leaves the room feeling under-filled. Advancing the seating improves sightlines to the artwork and creates a cozier atmosphere in this {arch_style} interior.",
            "measurement_cm": 15,
            "category": "seating_layout",
            "difficulty": "easy",
            "tools_needed": ["measuring_tape", "furniture_sliders"]
        })
    elif coverage > 0.55:
        changes.append({
            "action": "Create breathing room",
            "detail": f"Move the primary seating 10-15 cm (4-6 inches) away from the focal wall. Pull the coffee table forward by 8 cm to maintain a 45 cm gap between table and sofa edge.",
            "rationale": f"At {coverage:.0%} coverage, the room feels dense. Creating negative space around the perimeter will make the {arch_style} architecture more legible.",
            "measurement_cm": -12,
            "category": "seating_layout",
            "difficulty": "easy",
            "tools_needed": ["measuring_tape", "furniture_sliders"]
        })
    
    # 2. Coffee table adjustment
    changes.append({
        "action": "Reposition coffee table",
        "detail": "Adjust the coffee table so its center aligns with the center of the sofa. The ideal distance between sofa edge and table edge is 40-45 cm (16-18 inches) — enough to reach comfortably without crowding.",
        "rationale": "Proper proportional alignment between seating and surface creates visual order. The current layout can benefit from this centering adjustment.",
        "measurement_cm": 5,
        "category": "surface_layout",
        "difficulty": "easy",
        "tools_needed": ["measuring_tape"]
    })
    
    # 3. Lighting adjustments
    if shadow in ("heavy", "moderate") or brightness in ("dark", "very_dark"):
        changes.append({
            "action": "Add layered lighting",
            "detail": "Install a floor lamp with a warm 2700K LED in the darkest corner (opposite the primary light source). Add a table lamp on the console or side table with a 40W-equivalent warm bulb. Consider dimmable overhead fixtures on separate switches.",
            "rationale": f"The room currently has {evenness} lighting with {shadow} shadows. Layered lighting at different heights creates depth and allows the room to transition from functional to ambient.",
            "measurement_cm": 0,
            "category": "lighting",
            "difficulty": "medium",
            "tools_needed": ["lamp", "warm_led_bulbs", "dimmer_switch"]
        })
    
    if evenness == "even" and brightness in ("bright", "very_bright"):
        changes.append({
            "action": "Add directional accent lighting",
            "detail": "Install a picture light above the primary artwork (2700K, 40° beam angle). Add a small task lamp on a side table or console to create pools of warm light that contrast with the general ambient brightness.",
            "rationale": f"With {brightness} ambient light, the room benefits from targeted accent lighting that draws attention to the artwork and creates visual hierarchy.",
            "measurement_cm": 0,
            "category": "lighting",
            "difficulty": "medium",
            "tools_needed": ["picture_light", "warm_led_bulb"]
        })
    
    # 4. Rug recommendation
    if coverage < 0.5:
        changes.append({
            "action": "Introduce or replace area rug",
            "detail": f"Add a wool or natural-fiber area rug measuring approximately 200×280 cm (for a standard seating area). The rug should extend at least 45 cm past the front edge of the sofa on all sides.",
            "rationale": "A well-proportioned rug anchors the seating area, defines the zone, and introduces texture that softens the room's acoustics and visual character.",
            "measurement_cm": 200,
            "category": "flooring",
            "difficulty": "medium",
            "tools_needed": ["measuring_tape"]
        })
    
    # 5. Window treatment
    changes.append({
        "action": "Evaluate window treatments",
        "detail": f"If windows are uncovered, add floor-to-ceiling drapes in a fabric that complements the room's {ctx['color_temperature']} palette. Mount the rod 15-20 cm above the window frame to visually raise the {ctx['ceiling_height_m']}m ceiling.",
        "rationale": "Properly hung drapes add softness, control light, and make the ceiling appear taller. They also frame the window as an architectural feature.",
        "measurement_cm": 20,
        "category": "window_treatment",
        "difficulty": "medium",
        "tools_needed": ["curtain_rod", "drapes", "drill", "level"]
    })
    
    # 6. Wall finish / paint
    changes.append({
        "action": "Refresh wall finish",
        "detail": f"Consider painting the accent wall behind the artwork in a tone 2-3 shades darker than the current {ctx['primary_color']} base. Alternatively, add a wallcovering with subtle texture (linen, grasscloth) to the primary wall.",
        "rationale": f"A distinct wall treatment behind the artwork creates a gallery-like setting and adds depth to the {arch_style} interior.",
        "measurement_cm": 0,
        "category": "wall_finish",
        "difficulty": "hard",
        "tools_needed": ["paint", "brushes", "roller", "painter_tape"]
    })
    
    # 7. Accessories
    changes.append({
        "action": "Curate decorative objects",
        "detail": "Add 3-5 curated objects on the coffee table or console: a stack of art books, a ceramic vessel, a small sculptural object. Limit the palette to neutrals with one accent piece in the room's accent tone.",
        "rationale": "Curated objects tell a story and make the room feel lived-in and intentional. They also provide scale references that help the eye appreciate the room's proportions.",
        "measurement_cm": 0,
        "category": "accessories",
        "difficulty": "easy",
        "tools_needed": []
    })
    
    # 8. Frame finish adjustment (align with artwork recommendations)
    changes.append({
        "action": "Update artwork framing",
        "detail": "If existing frames are mixed finishes, unify them. For the statement piece, use a frame finish that echoes the room's hardware — brass or brushed nickel for cool tones, oil-rubbed bronze for warm tones.",
        "rationale": "Consistent frame finishes signal curation rather than accumulation. The frame should be the bridge between the artwork and the room, not a competing element.",
        "measurement_cm": 0,
        "category": "framing",
        "difficulty": "medium",
        "tools_needed": ["framing_services"]
    })
    
    return changes


def generate_color_palette_recs(ctx):
    """Generate color palette extension recommendations."""
    return {
        "wall_color_recommendation": {
            "primary": f"A warm neutral like Sherwin-Williams 'Accessible Beige' or Benjamin Moore 'Edgecomb Gray' — complements {ctx['primary_color']}",
            "accent_wall": f"A deeper tone like Farrow & Ball 'Drop Cloth' or Sherwin-Williams 'Urbane Bronze' — creates depth behind artwork",
            "trim": "Crisp white with a hint of warmth — Benjamin Moore 'Cloud White' or Farrow & Ball 'Strong White'"
        },
        "texture_recommendations": [
            "Linen or nubby wool upholstery to absorb sound and add softness",
            "Brass or brushed nickel light fixtures for warm metallic contrast",
            "Natural wood accents (walnut or oak) to ground the color scheme",
            "Ceramic or stone surfaces for organic tactile variety"
        ]
    }


def generate_styling_guide(ctx, quiet=False):
    """Complete Step 3: generate the full styling guide."""
    if not quiet:
        print(f"Galerie Noire — Styling Guide Engine (Step 3)")
        print(f"Room: {ctx['room_type']} ({ctx['architecture_style']})")
        print("=" * 50)
    
    if not quiet:
        print("\n[1/3] Analyzing room layout...")
    layout_changes = generate_layout_changes(ctx)
    if not quiet:
        print(f"       {len(layout_changes)} layout/styling changes recommended")
    
    if not quiet:
        print("[2/3] Developing color & material palette...")
    color_recs = generate_color_palette_recs(ctx)
    
    if not quiet:
        print("[3/3] Compiling styling guide...")
    
    styling_guide = {
        "room_summary": {
            "room_type": ctx["room_type"],
            "architecture_style": ctx["architecture_style"],
            "ceiling_height_m": ctx["ceiling_height_m"],
            "color_temperature": ctx["color_temperature"],
            "lighting_mood": ctx["lighting_mood"]
        },
        "layout_changes": layout_changes,
        "color_and_material": color_recs,
        "styling_philosophy": (
            f"This {ctx['architecture_style']} room benefits from {len(layout_changes)} targeted adjustments "
            f"that respect its {ctx['color_temperature']}, {ctx['lighting_mood']} character. "
            f"The guiding principle is subtraction before addition — remove visual clutter, then "
            f"add intentional pieces that serve both function and atmosphere."
        ),
        "priority_order": [
            { "order": 1, "action": "Seating and table layout", "rationale": "Foundation of the room's function" },
            { "order": 2, "action": "Lighting adjustments", "rationale": "Transforms atmosphere more than any other change" },
            { "order": 3, "action": "Rug and floor covering", "rationale": "Anchors the zone and adds texture" },
            { "order": 4, "action": "Wall finish and framing", "rationale": "Sets the gallery context for artwork" },
            { "order": 5, "action": "Window treatments", "rationale": "Controls light and adds softness" },
            { "order": 6, "action": "Decorative accessories", "rationale": "Personalizes the space last" }
        ]
    }
    
    return styling_guide



if __name__ == "__main__":
    """CLI entry point for standalone styling guide."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python styling_guide.py <room_profile.json> [--json]")
        sys.exit(1)
    
    profile_path = sys.argv[1]
    quiet = "--json" in sys.argv
    
    profile = load_room_profile(profile_path)
    ctx = extract_context(profile)
    result = generate_styling_guide(ctx, quiet=quiet)
    
    if quiet:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 60)
        print("STYLING GUIDE (JSON)")
        print("=" * 60)
        print(json.dumps(result, indent=2))
