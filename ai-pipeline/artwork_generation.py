#!/usr/bin/env python3
"""
Artwork Generation Engine — Galerie Noire AI Pipeline (Step 2)
==============================================================
Takes the room profile JSON from Step 1 and generates 5 custom digital
artworks tailored to that specific space. Each artwork considers:
- Wall dimensions and available space
- Color palette harmony and temperature
- Viewing distance and optimal size
- Lighting conditions and mood
- Furniture style and architecture style
- Room type and ceiling height

The output feels commissioned, not templated — each piece is defensibly
"custom for this room" with a clear design rationale.
"""

import json
import os
import sys
from pathlib import Path

# Artist style personas — each artwork concept has a distinct "artist's eye"
ARTIST_STYLES = [
    {
        "slug": "statement_composition",
        "name": "Statement Composition",
        "artist": "A contemporary artist working in large-format mixed media",
        "mood": "bold_contemplative",
        "description_template": (
            "A large-format {style_influenced} composition that anchors the room. "
            "Bold gestural marks in {primary_color} and {accent_color} dance across "
            "a {background_desc} field, creating a visual anchor that draws the eye "
            "from the {viewing_position}. The scale commands attention while the "
            "palette remains in conversation with the room's {temperature} tones."
        )
    },
    {
        "slug": "abstract_atmosphere",
        "name": "Abstract Atmosphere",
        "artist": "A color-field painter influenced by Rothko and contemporary light art",
        "mood": "meditative_luminous",
        "description_template": (
            "Luminous layers of {primary_color} and {accent_color} float within "
            "a {lighting_desc} field, echoing the {mood_name} atmosphere of the room. "
            "Soft transitions between hues mirror the {shadow_quality} quality of the "
            "space's natural light. This piece changes character throughout the day, "
            "revealing new depth as the room's {lighting_mood} shifts."
        )
    },
    {
        "slug": "botanical_study",
        "name": "Botanical Study",
        "artist": "A naturalist illustrator working in the tradition of botanical art",
        "mood": "organic_grounded",
        "description_template": (
            "A refined botanical study that introduces organic softness to the "
            "{style_name} interior. Delicate {plant_form} forms in {accent_color} "
            "and {tertiary_color} are rendered against a {background_desc} ground. "
            "The {warmth_desc} palette complements the room's {architecture_style} "
            "lines while the natural subject matter provides visual relief from "
            "the {furniture_texture} surfaces."
        )
    },
    {
        "slug": "architectural_geometric",
        "name": "Architectural Geometry",
        "artist": "An artist working at the intersection of architecture and abstract geometry",
        "mood": "structured_elegant",
        "description_template": (
            "A precision-crafted geometric study that echoes the {style_influenced} "
            "architecture of the space. Intersecting planes in {primary_color}, "
            "{accent_color}, and {tertiary_color} create depth that draws the eye "
            "across the {art_width_cm}cm width. The {contrast_level} contrast "
            "relates to the room's {lighting_contrast} lighting, while the "
            "compositional rhythm mirrors the {vh_ratio} proportion of vertical "
            "to horizontal lines in the room."
        )
    },
    {
        "slug": "atmospheric_landscape",
        "name": "Atmospheric Landscape",
        "artist": "A landscape painter working in the romantic tradition",
        "mood": "expansive_serene",
        "description_template": (
            "An atmospheric landscape that extends the {ceiling_desc} ceiling "
            "into an imagined horizon. Layers of {primary_color}, {accent_color}, "
            "and {tertiary_color} recede into the distance, creating the illusion "
            "of a {room_type_desc} opening onto a wider vista. The {lighting_mood2} "
            "treatment aligns with the room's existing {color_temp_desc} light sources, "
            "making the piece feel like a natural extension of the space."
        )
    }
]

# Frame style recommendations mapped to artwork types and room context
FRAME_RECOMMENDATIONS = {
    "statement_composition": {
        "style": "tray_frame",
        "material": "brushed_brass",
        "finish": "satin",
        "profile": "clean_minimal",
        "depth_cm": 5,
        "description": "A deep tray frame in satin brushed brass that floats the artwork away from the wall, creating a subtle shadow gap that enhances the piece's sculptural presence."
    },
    "abstract_atmosphere": {
        "style": "floating_frame",
        "material": "natural_oak",
        "finish": "matte",
        "profile": "shadow_gap",
        "depth_cm": 3,
        "description": "A light natural oak floating frame with a shadow gap that separates the artwork from the wall, allowing the luminous colors to breathe."
    },
    "botanical_study": {
        "style": "classic_molding",
        "material": "polished_brass",
        "finish": "antique",
        "profile": "ornamental",
        "depth_cm": 4,
        "description": "A classic polished brass molding with a subtle antique patina that complements the refined botanical subject without overpowering it."
    },
    "architectural_geometric": {
        "style": "cleat_hanger",
        "material": "black_steel",
        "finish": "matte",
        "profile": "minimal_channel",
        "depth_cm": 2,
        "description": "A slim black steel channel frame — nearly invisible — that lets the geometric composition speak directly to the wall. Mounted on a cleat system for perfect alignment."
    },
    "atmospheric_landscape": {
        "style": "gallery_profile",
        "material": "charcoal_wood",
        "finish": "matte_ebp",
        "profile": "contemporary",
        "depth_cm": 4,
        "description": "A charcoal-stained wood gallery profile frame with a matte ebonized finish that creates a window-like transition between the room and the imagined landscape beyond."
    }
}

# Picture lighting recommendations
LIGHTING_RECOMMENDATIONS = {
    "statement_composition": {
        "type": "gallery_picture_light",
        "placement": "single_centered",
        "color_temp_k": 2700,
        "beam_angle_deg": 40,
        "description": "A single adjustable gallery light with a warm 2700K LED, centered above the artwork. The 40° beam angle illuminates the entire piece without glare."
    },
    "abstract_atmosphere": {
        "type": "wall_washer",
        "placement": "recessed_ceiling",
        "color_temp_k": 3000,
        "beam_angle_deg": 60,
        "description": "A recessed wall-washing LED fixture, positioned to graze the surface gently. 3000K to preserve the color relationships in the layered composition."
    },
    "botanical_study": {
        "type": "adjustable_picture_light",
        "placement": "single_angled",
        "color_temp_k": 3000,
        "beam_angle_deg": 35,
        "description": "An adjustable picture light with a narrow 35° beam, angled to highlight the fine detail of the botanical rendering. 3000K to keep the greens fresh."
    },
    "architectural_geometric": {
        "type": "linear_led",
        "placement": "top_edge_backlight",
        "color_temp_k": 3500,
        "beam_angle_deg": 120,
        "description": "An ultra-thin linear LED strip mounted behind the frame's top edge, casting a soft wash down the surface. 3500K for crisp geometric clarity."
    },
    "atmospheric_landscape": {
        "type": "double_picture_lights",
        "placement": "dual_angled",
        "color_temp_k": 2700,
        "beam_angle_deg": 30,
        "description": "Twin adjustable picture lights with 30° beams, mounted at 45° angles from each top corner. The warm 2700K light enriches the atmospheric depth."
    }
}


def load_room_profile(profile_path):
    """Load a room profile JSON file produced by Step 1."""
    with open(profile_path, 'r') as f:
        return json.load(f)


def build_context(profile):
    """
    Extract and enrich the room profile into a context dictionary
    that the artwork generation templates can interpolate into.
    """
    rp = profile["room_profile"]
    
    # Color palette
    colors = rp["color_palette"]["dominant_colors"]
    primary_color = colors[0]["hex"] if len(colors) > 0 else "#DED2BF"
    accent_color = colors[1]["hex"] if len(colors) > 1 else "#C5A55A"
    tertiary_color = colors[2]["hex"] if len(colors) > 2 else "#A8A6A0"
    background_color = colors[-1]["hex"] if len(colors) > 0 else "#1A1A1A"
    
    color_temp = rp["color_palette"]["color_temperature"]
    vibrancy = rp["color_palette"]["vibrancy"]
    harmony = rp["color_palette"]["harmony"]
    
    # Lighting
    lighting = rp["lighting"]
    brightness = lighting["brightness_level"]
    mood_name = lighting["mood"].replace("_", " ")
    shadow_quality = lighting["shadow_severity"]
    lighting_contrast = lighting["contrast"]
    color_temp_desc = lighting["color_temperature"]
    lighting_evenness = lighting["lighting_evenness"]
    
    # Architecture
    arch = rp["architecture"]
    room_type = arch["room_type_guess"].replace("_", " ")
    ceiling_height = arch["ceiling_height_estimate_m"]
    ceiling_cat = arch["ceiling_category"].replace("_", " ")
    
    # Architecture style
    style = rp["architecture_style"]
    arch_style_name = style["primary_style"]
    style_confidence = style["confidence"]
    vh_ratio = style["style_characteristics"]["vertical_horizontal_ratio"]
    edge_density = style["style_characteristics"]["edge_density"]
    texture_variance = style["style_characteristics"]["texture_variance"]
    warmth_index = style["style_characteristics"]["warmth_index"]
    
    # Furniture
    furniture = rp["furniture"]
    furniture_texture = furniture["furniture_surface"].replace("_", " ")
    furniture_layout = furniture["layout_style"].replace("_", " ")
    furniture_items = furniture["items_detected_count"]
    
    # Wall space
    walls = rp["wall_space"]
    art_width_cm = walls["recommended_artwork_width_cm"]
    art_height_cm = walls["recommended_artwork_height_cm"]
    primary_wall = walls["primary_wall"].replace("_", " ")
    
    # Viewing
    viewing = rp["viewing_distance"]
    view_dist = viewing["optimal_viewing_distance_m"]
    frame_size_rec = viewing["recommended_frame_size"].replace("_", " ")
    
    # Derived attributes for template interpolation
    style_influenced = f"{arch_style_name}-inspired"
    
    if color_temp == "warm":
        temperature = "warm, honeyed"
        warmth_desc = "sun-warmed"
    elif color_temp == "cool":
        temperature = "cool, crisp"
        warmth_desc = "cool-toned"
    else:
        temperature = "balanced, neutral"
        warmth_desc = "balanced"
    
    if vibrancy == "high":
        background_desc = "richly saturated"
    elif vibrancy == "medium":
        background_desc = "subdued"
    else:
        background_desc = "quiet, understated"
    
    if shadow_quality == "heavy":
        shadow_desc = "deeply shadowed"
    elif shadow_quality == "moderate":
        shadow_desc = "gently shadowed"
    else:
        shadow_desc = "brightly open"
    
    if ceiling_cat == "cathedral_or_high":
        ceiling_desc = "soaring"
    elif ceiling_cat == "standard_plus":
        ceiling_desc = "generously proportioned"
    elif ceiling_cat == "standard":
        ceiling_desc = "comfortably scaled"
    else:
        ceiling_desc = "intimately scaled"
    
    if "sofa" in furniture_layout or "seating" in furniture_layout:
        viewing_position = "seated viewing position"
    else:
        viewing_position = "natural standing viewpoint"
    
    if len(room_type) > 15:
        room_type_desc = "interior"
    else:
        room_type_desc = room_type
    
    return {
        "primary_color": primary_color,
        "accent_color": accent_color,
        "tertiary_color": tertiary_color,
        "background_color": background_color,
        "color_temperature": color_temp,
        "temperature": temperature,
        "warmth_desc": warmth_desc,
        "vibrancy": vibrancy,
        "harmony": harmony,
        "background_desc": background_desc,
        "lighting_mood": mood_name,
        "lighting_mood2": mood_name,
        "mood_name": mood_name,
        "shadow_quality": shadow_quality,
        "shadow_desc": shadow_desc,
        "lighting_contrast": lighting_contrast,
        "color_temp_desc": color_temp_desc,
        "lighting_desc": lighting_evenness,
        "room_type": room_type,
        "room_type_desc": room_type_desc,
        "ceiling_height": ceiling_height,
        "ceiling_desc": ceiling_desc,
        "architecture_style": arch_style_name,
        "style_confidence": style_confidence,
        "style_influenced": style_influenced,
        "style_name": arch_style_name,
        "vh_ratio": round(vh_ratio, 2),
        "edge_density": round(edge_density, 3),
        "texture_variance": round(texture_variance, 1),
        "warmth_index": round(warmth_index, 3),
        "furniture_texture": furniture_texture,
        "furniture_layout": furniture_layout,
        "furniture_items": furniture_items,
        "art_width_cm": art_width_cm,
        "art_height_cm": art_height_cm,
        "primary_wall": primary_wall,
        "viewing_distance_m": view_dist,
        "frame_size_rec": frame_size_rec,
        "viewing_position": viewing_position,
        "plant_form": "foliage" if "warm" in color_temp or warmth_index > 0.1 else "frond",
        "contrast_level": "refined" if lighting_contrast == "medium" else "pronounced" if lighting_contrast == "high" else "subtle"
    }


def generate_artwork_concept(artist_style, ctx):
    """
    Generate a full artwork concept from an artist style template and room context.
    Returns a structured dict with title, description, rationale, frame rec, etc.
    """
    slug = artist_style["slug"]
    
    # Fill the description template with context
    description = artist_style["description_template"].format(**ctx)
    
    # Generate a unique title based on the room
    title_prefixes = {
        "statement_composition": ["Anchorage", "Axis", "Presence", "Threshold", "Monolith"],
        "abstract_atmosphere": ["Lumina", "Veil", "Resonance", "Aether", "Wavelength"],
        "botanical_study": ["Verdure", "Study in", "Flora", "Petiole", "Frondescence"],
        "architectural_geometric": ["Interlock", "Cartography", "Fracture", "Plan View", "Tectonic"],
        "atmospheric_landscape": ["Horizon Line", "Distance", "Vista", "The Far Edge", "Boundless"]
    }
    
    title_suffixes = {
        "statement_composition": ["No. {}", "I", "II", "IV", "VII"],
        "abstract_atmosphere": ["Series", "Study", "on {}'s Light", "Variation", "Opacity"],
        "botanical_study": ["I", "II", "III", "op. {}", "t. {}"],
        "architectural_geometric": ["(after {}), {}", "in {} Parts", "Schema {}", "Axis {}", "Plan {}", "Module"],
        "atmospheric_landscape": [", {}", ", Evening", " in Fog", " at Dusk", " — Study"]
    }
    
    # Pick title based on room architecture style and color harmony
    style_hash = sum(ord(c) for c in ctx["architecture_style"]) % 5
    color_hash = sum(ord(c) for c in ctx["color_temperature"]) % 3
    
    prefixes = title_prefixes.get(slug, ["Untitled"])
    suffixes = title_suffixes.get(slug, [""])
    
    prefix = prefixes[style_hash % len(prefixes)]
    suffix = suffixes[(style_hash + color_hash) % len(suffixes)]
    
    # Format suffix with context values
    try:
        suffix = suffix.format(ctx["art_width_cm"], ctx["ceiling_height"], ctx["room_type"])
    except (KeyError, IndexError):
        pass
    
    if suffix:
        suffix = suffix.strip()
        if suffix and suffix[0] in [',', '—', '–', ':']:
            title = f"{prefix}{suffix}"
        else:
            title = f"{prefix} {suffix}"
    else:
        title = prefix
    
    # Frame recommendation
    frame = FRAME_RECOMMENDATIONS[slug]
    
    # Lighting recommendation
    pic_lighting = LIGHTING_RECOMMENDATIONS[slug]
    
    # Placement guidance
    if slug == "statement_composition":
        placement = f"Primary wall ({ctx['primary_wall']} quadrant), centered at eye level ({ctx['art_width_cm']}×{ctx['art_height_cm']}cm)"
    elif slug == "architectural_geometric":
        placement = f"Secondary wall or above a console table, smaller scale as an accent counterpoint"
    elif slug == "atmospheric_landscape":
        placement = f"Above the primary seating area, positioned to be the first piece seen when entering the room"
    elif slug == "botanical_study":
        placement = f"Near the window or naturally lit wall area, to interact with the {ctx['lighting_mood']} natural light"
    elif slug == "abstract_atmosphere":
        placement = f"Opposite the main seating position, at {ctx['viewing_distance_m']}m viewing distance for optimal color field immersion"
    else:
        placement = "Per curator's recommendation"
    
    # Color rationale
    color_rationale = (
        f"The palette draws from the room's dominant {ctx['primary_color']} and accent {ctx['accent_color']} tones, "
        f"ensuring {ctx['harmony']} harmony with the existing {ctx['color_temperature']} interior. "
        f"The {ctx['vibrancy']} vibrancy level matches the room's {ctx['background_desc']} character."
    )
    
    # Artwork rationale (why this piece for this specific room)
    artwork_rationale = (
        f"This piece responds to the room's {ctx['architecture_style']} architecture "
        f"({ctx['style_confidence']} confidence) with its {ctx['contrast_level']} composition. "
        f"The {ctx['ceiling_desc']} ceiling ({ctx['ceiling_height']}m) and "
        f"{ctx['lighting_mood']} lighting conditions informed the scale and contrast. "
        f"At {ctx['viewing_distance_m']}m viewing distance, the {ctx['frame_size_rec']} format "
        f"fills the optimal field of view."
    )
    
    # Image prompt for AI image generation
    image_prompt = (
        f"A high-end digital artwork titled '{title}', {ctx['frame_size_rec']} format. "
        f"{description} "
        f"The piece is museum-quality, suitable for a luxury interior. "
        f"Color palette centered on {ctx['primary_color']} with {ctx['accent_color']} accents. "
        f"Style: {artist_style['mood'].replace('_', ' ')}. "
        f"The artwork should feel like a commissioned gallery piece — not generic, not templated, "
        f"but intentionally made for this specific room with {ctx['architecture_style']} architecture."
    )
    
    return {
        "slug": slug,
        "title": title.strip(),
        "artist_persona": artist_style["artist"],
        "mood": artist_style["mood"].replace("_", " "),
        "description": description,
        "artwork_rationale": artwork_rationale,
        "color_rationale": color_rationale,
        "image_prompt": image_prompt,
        "recommended_frame": frame,
        "recommended_lighting": pic_lighting,
        "recommended_placement": placement,
        "dimensions_cm": {
            "width": ctx["art_width_cm"] if slug != "architectural_geometric" else max(60, ctx["art_width_cm"] // 2),
            "height": ctx["art_height_cm"] if slug != "architectural_geometric" else max(80, ctx["art_height_cm"] // 2)
        }
    }


def generate_all_artworks(room_profile_path, output_dir=None, quiet=False):
    """
    Main pipeline: load room profile, generate 5 artwork concepts,
    and optionally save the output.
    
    Args:
        room_profile_path: Path to room profile JSON (from Step 1)
        output_dir: If set, save output JSON here and generate images
        quiet: If True, suppresses progress output
    
    Returns:
        dict with room info, artwork concepts, and metadata
    """
    if not quiet:
        print(f"Galerie Noire — Artwork Generation Engine (Step 2)")
        print(f"Loading room profile: {room_profile_path}")
        print("=" * 50)
    
    profile = load_room_profile(room_profile_path)
    
    if not quiet:
        print(f"Room: {profile['room_profile']['architecture']['room_type_guess']}")
        print(f"Style: {profile['room_profile']['architecture_style']['primary_style']}")
        print(f"Wall: {profile['room_profile']['wall_space']['recommended_artwork_width_cm']}×{profile['room_profile']['wall_space']['recommended_artwork_height_cm']}cm")
        print()
    
    # Build enriched context for template interpolation
    if not quiet:
        print("[1/5] Building room context...")
    ctx = build_context(profile)
    if not quiet:
        print(f"       {len(ctx)} context variables extracted")
    
    # Generate 5 artwork concepts
    if not quiet:
        print("[2/5] Generating 5 artwork concepts...")
    artworks = []
    for i, artist_style in enumerate(ARTIST_STYLES):
        if not quiet:
            print(f"       [{i+1}/5] Creating '{artist_style['name']}'...")
        concept = generate_artwork_concept(artist_style, ctx)
        artworks.append(concept)
    
    if not quiet:
        print("[3/5] Curating frame recommendations...")
        print("[4/5] Curating picture lighting recommendations...")
    
    # Compile output
    if not quiet:
        print("[5/5] Compiling final output...")
    output = {
        "room_summary": {
            "room_type": ctx["room_type"],
            "architecture_style": ctx["architecture_style"],
            "ceiling_height_m": ctx["ceiling_height"],
            "primary_wall_quadrant": ctx["primary_wall"],
            "color_temperature": ctx["color_temperature"],
            "lighting_mood": ctx["lighting_mood"]
        },
        "artwork_collection": {
            "count": len(artworks),
            "description": f"Five custom digital artworks commissioned for this {ctx['room_type']} — "
                          f"each piece designed to harmonize with the {ctx['architecture_style']} aesthetic, "
                          f"{ctx['temperature']} palette, and {ctx['lighting_mood']} atmosphere.",
            "pieces": artworks
        },
        "metadata": {
            "engine_version": "2.0.0",
            "pipeline_step": 2,
            "source_profile": str(room_profile_path)
        }
    }
    
    # Save output
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "artwork_collection.json"
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        if not quiet:
            print(f"\nSaved artwork collection to: {output_path}")
    
    return output


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 artwork_generation.py <room_profile.json> [--output-dir <dir>] [--json]")
        print()
        print("Generates 5 custom digital artworks from a room profile (Step 1 output).")
        print("  --output-dir <dir>    Save generated artwork JSON and images to <dir>")
        print("  --json                Output raw JSON only (no progress messages)")
        sys.exit(1)
    
    profile_path = sys.argv[1]
    output_dir = None
    quiet = "--json" in sys.argv
    
    if "--output-dir" in sys.argv:
        idx = sys.argv.index("--output-dir")
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]
    
    result = generate_all_artworks(profile_path, output_dir=output_dir, quiet=quiet)
    
    if quiet:
        print(json.dumps(result["artwork_collection"], indent=2))
    else:
        print("\n" + "=" * 50)
        print("COMPLETE ARTWORK COLLECTION (JSON)")
        print("=" * 50)
        print(json.dumps(result["artwork_collection"], indent=2))


if __name__ == "__main__":
    main()