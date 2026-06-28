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
    surface = furniture.get("furniture_surface", "varied_textured")
    furniture_types = furniture.get("furniture_types", ["undetermined"])
    furniture_confidence = furniture.get("confidence", "low")
    
    style_confidence = style.get("confidence", "low")
    
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
        "style_confidence": style_confidence,
        "furniture_layout": layout,
        "furniture_coverage": coverage,
        "furniture_count": items_count,
        "furniture_types": furniture_types,
        "furniture_confidence": furniture_confidence,
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
        "action": "Consider window treatments",
        "detail": f"If the room has windows, floor-to-ceiling drapes in a fabric that complements the room's {ctx['color_temperature']} palette can add softness. Mount the rod 15-20 cm above the window frame to visually raise the {ctx['ceiling_height_m']}m ceiling.",
        "rationale": "Window treatments control light, add texture, and frame windows as architectural features. This recommendation depends on confirming window placement from additional angles.",
        "measurement_cm": 20,
        "category": "window_treatment",
        "difficulty": "medium",
        "tools_needed": ["curtain_rod", "drapes", "drill", "level"],
        "note": "This assumes windows confirmed present in the room — verify from other photos"
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
    
    # 8. Frame finish adjustment
    changes.append({
        "action": "Select artwork frame finish",
        "detail": "For new artwork, choose a unified frame finish. Based on the room's color temperature, opt for warm metallic tones (gold, bronze) for warm rooms or cool tones (silver, black) for cooler palettes. The frame should complement, not compete with, the artwork.",
        "rationale": "Consistent frame finishes signal curation rather than accumulation. The frame bridges the artwork and the room's existing character.",
        "measurement_cm": 0,
        "category": "framing",
        "difficulty": "medium",
        "tools_needed": ["framing_services"],
        "note": "Frame material recommendation is based on room color temperature — confirm with physical material swatches"
    })
    
    return changes


def generate_color_palette_recs(ctx):
    """Generate color palette extension recommendations."""
    warmth = ctx["color_temperature"]
    primary = ctx["primary_color"]
    
    # Determine appropriate wall tone based on detected color temperature
    if warmth == "warm":
        base_note = "a warm off-white or cream"
        accent_note = "a deeper earthy tone (terracotta, warm taupe)"
    elif warmth == "cool":
        base_note = "a cool gray or soft blue-gray"
        accent_note = "a deeper slate or charcoal"
    else:
        base_note = "a versatile neutral (greige, soft stone)"
        accent_note = "a deeper neutral that adds depth"
    
    return {
        "wall_color_recommendation": {
            "primary": f"{base_note.capitalize()} — complements detected base {primary}",
            "accent_wall": f"{accent_note} — creates depth behind artwork",
            "trim": "A slightly lighter version of the wall color or a warm white for contrast"
        },
        "texture_recommendations": [
            "Soft upholstery (linen, wool, cotton) to add tactile warmth",
            "Metallic light fixtures in a finish that suits the room's warm/cool balance",
            "Natural wood accents for organic contrast",
            "Ceramic or stone surfaces for tactile variety"
        ],
        "disclaimer": "These are general recommendations based on detected color palette and lighting. Confirm with physical samples before purchasing."
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
            "style_confidence": ctx["style_confidence"],
            "ceiling_height_m": ctx["ceiling_height_m"],
            "color_temperature": ctx["color_temperature"],
            "lighting_mood": ctx["lighting_mood"],
            "furniture_types": ctx["furniture_types"],
            "furniture_count": ctx["furniture_count"],
            "furniture_confidence": ctx["furniture_confidence"]
        },
        "analysis_limitations": {
            "style_note": "Architecture style is inferred from statistical analysis of color, edge, and texture patterns. For mixed or neutral rooms, multiple styles may score similarly.",
            "furniture_note": "Furniture detection uses edge-based estimation and cannot identify specific materials, brands, or finishes. All furniture counts are approximate.",
            "material_note": "Specific materials (brass, walnut, marble, etc.) are not detectable from standard room photos. Any material suggestions in recommendations are style-compatible proposals, not confirmed existing features.",
            "general": "This analysis is based on a single photograph. Room characteristics visible in other angles or lighting conditions may differ. All recommendations should be verified in person."
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


# ─── Step 4: Shopping Guide ───────────────────────────────────────────────────

RETAILERS = {
    "luxury": {
        "name": "Luxury",
        "retailers": ["Restoration Hardware", "Design Within Reach", "Artefact", "Ralph Lauren Home"],
        "description": "Investment pieces for clients who value heirloom quality"
    },
    "premium": {
        "name": "Premium",
        "retailers": ["CB2", "Crate & Barrel", "West Elm", "Pottery Barn"],
        "description": "High-quality design at accessible investment levels"
    },
    "budget": {
        "name": "Budget",
        "retailers": ["IKEA", "Target (Project 62)", "World Market", "Amazon (Rivet)"],
        "description": "Smart style on a practical timeline"
    }
}


def get_seating_recs(ctx):
    """Seating recommendations across tiers."""
    style = ctx["architecture_style"].lower()
    is_modern = "modern" in style or "contemporary" in style
    is_traditional = "traditional" in style or "classic" in style or "eclectic" in style
    is_midcentury = "mid century" in style
    is_scandi = "scandinavian" in style
    
    if is_midcentury or is_scandi:
        sofa_style = "clean-lined with tapered legs"
        chair_style = "shell or scoop chair"
    elif is_modern:
        sofa_style = "low-profile with track arms"
        chair_style = "leather or boucle lounge chair"
    elif is_traditional:
        sofa_style = "rolled-arm with skirt or exposed legs"
        chair_style = "wingback or club chair"
    else:
        sofa_style = "versatile with minimal profile"
        chair_style = "accent chair in complementary texture"
    
    return {
        "sofa": {
            "tiers": {
                "luxury": {
                    "product": f"RH Cloud Couch or RH Maxwell Sofa — {sofa_style}",
                    "retailer": "Restoration Hardware",
                    "price_range": "$4,000 - $8,000",
                    "note": "Deep seat depth and down-blend fill for lounging. Choose performance fabric in a warm neutral."
                },
                "premium": {
                    "product": f"{'CB2 Oak Park Sofa' if is_midcentury else 'Crate & Barrel Lounge II'} — {sofa_style}",
                    "retailer": "CB2 / Crate & Barrel",
                    "price_range": "$1,500 - $3,000",
                    "note": "Excellent proportions for standard room sizes. Add a matching ottoman."
                },
                "budget": {
                    "product": f"IKEA SÖDERHAMN or KIVIK sectional — modular {sofa_style}",
                    "retailer": "IKEA",
                    "price_range": "$800 - $1,500",
                    "note": "Modular sections offer flexibility. Upgrade with custom covers from Bemz or Comfort Works."
                }
            },
            "recommended_tier": "premium" if ctx["furniture_coverage"] < 0.4 else "budget"
        },
        "accent_chairs": {
            "tiers": {
                "luxury": {
                    "product": f"DWR {chair_style} by {'Eames' if is_midcentury else 'a design icon'}",
                    "retailer": "Design Within Reach",
                    "price_range": "$2,000 - $4,500",
                    "note": "An investment piece that becomes the room's signature. Consider a leather or boucle finish."
                },
                "premium": {
                    "product": f"{'West Elm Harris' if is_midcentury else 'Pottery Barn Turner'} accent chair — {chair_style}",
                    "retailer": "West Elm / Pottery Barn",
                    "price_range": "$700 - $1,500",
                    "note": "Well-made with good fabric options. Order swatches to confirm color match."
                },
                "budget": {
                    "product": f"IKEA STRANDMON or TULLSTA — {chair_style} alternative",
                    "retailer": "IKEA",
                    "price_range": "$300 - $600",
                    "note": "Surprisingly comfortable. Choose a slipcovered version for easy cleaning."
                }
            },
            "recommended_tier": "premium"
        }
    }


def get_lighting_recs(ctx):
    """Lighting recommendations across tiers."""
    mood = ctx["lighting_mood"]
    is_cozy = "cozy" in mood or "soft" in mood
    is_bright = "bright" in mood or "crisp" in mood
    
    return {
        "floor_lamp": {
            "tiers": {
                "luxury": {
                    "product": "RH Architectural Floor Lamp in burnished brass",
                    "retailer": "Restoration Hardware",
                    "price_range": "$1,200 - $2,500",
                    "note": "Sculptural presence that doubles as art. A metallic finish provides a subtle accent."
                },
                "premium": {
                    "product": "CB2 Tripod Floor Lamp in black or brass",
                    "retailer": "CB2",
                    "price_range": "$300 - $600",
                    "note": "Clean silhouette that doesn't compete with the artwork. Add a warm dimmable bulb."
                },
                "budget": {
                    "product": "IKEA HEKTOGRAM or RANARP floor lamp",
                    "retailer": "IKEA",
                    "price_range": "$80 - $150",
                    "note": "Classic adjustable design. Paint the base in a metallic finish for a custom look."
                }
            },
            "recommended_tier": "premium",
            "bulb_recommendation": "2700K warm LED, dimmable, 800+ lumens"
        },
        "picture_light": {
            "tiers": {
                "luxury": {
                    "product": "Hudson Valley Ormand Picture Light in aged brass",
                    "retailer": "Restoration Hardware / Visual Comfort",
                    "price_range": "$400 - $800",
                    "note": "Museum-quality picture lighting with adjustable arm. Hardwired for clean installation."
                },
                "premium": {
                    "product": "CB2 Caged Picture Light or West Elm Brass Picture Light",
                    "retailer": "CB2 / West Elm",
                    "price_range": "$150 - $300",
                    "note": "Plug-in option available. Choose a 40° beam angle for artwork up to 150cm wide."
                },
                "budget": {
                    "product": "IKEA RIKTIG LED strip or battery-operated picture light",
                    "retailer": "IKEA / Amazon",
                    "price_range": "$20 - $80",
                    "note": "Adhesive LED strip behind the frame for a floating glow effect. Easy no-wire installation."
                }
            },
            "recommended_tier": "luxury" if is_bright else "premium"
        },
        "table_lamp": {
            "tiers": {
                "luxury": {
                    "product": "Artefact or RH Ceramic Table Lamp in cream glaze",
                    "retailer": "Restoration Hardware / Artefact",
                    "price_range": "$500 - $1,200",
                    "note": "Hand-thrown ceramic base with linen shade. Provides warm task and ambient light."
                },
                "premium": {
                    "product": "Pottery Barn Belden or West Elm Sphere Table Lamp",
                    "retailer": "Pottery Barn / West Elm",
                    "price_range": "$150 - $350",
                    "note": "Weighted base and tapered drum shade. Pair with a 3-way dimmable bulb."
                },
                "budget": {
                    "product": "IKEA TÄRNABY or Target Project 62 table lamp",
                    "retailer": "IKEA / Target",
                    "price_range": "$40 - $90",
                    "note": "Simple ceramic or metal base. Replace shade with a linen option for a more premium look."
                }
            },
            "recommended_tier": "premium"
        }
    }


def get_rug_recs(ctx):
    """Rug recommendations across tiers."""
    width_cm = ctx["artwork_width_cm"]
    return {
        "area_rug": {
            "suggested_size_cm": f"200×280 or 240×300",
            "fit_note": "Rug should extend at least 45cm past the sofa edges on all sides",
            "tiers": {
                "luxury": {
                    "product": "RH Belgian Flax Linen Rug in natural or RH Moroccan Wool Rug",
                    "retailer": "Restoration Hardware",
                    "price_range": "$2,000 - $5,000",
                    "note": "Hand-knotted wool or flax for heirloom quality. Neutral tones anchor without competing."
                },
                "premium": {
                    "product": "West Elm Geo Trellis or CB2 Hand-Knotted Wool Rug",
                    "retailer": "West Elm / CB2",
                    "price_range": "$600 - $1,500",
                    "note": "Good wool blend with subtle pattern. Low pile for easy furniture movement."
                },
                "budget": {
                    "product": "IKEA STOENSE flatweave or LOHALS jute rug",
                    "retailer": "IKEA",
                    "price_range": "$100 - $300",
                    "note": "Natural fibers add texture without cost. Layer two smaller rugs for a designer look."
                }
            },
            "recommended_tier": "premium"
        }
    }


def get_table_recs(ctx):
    """Coffee/side table recommendations."""
    return {
        "coffee_table": {
            "tiers": {
                "luxury": {
                    "product": "RH Modern Trestle Table in walnut or DWR Nelson Platform Bench",
                    "retailer": "Restoration Hardware / Design Within Reach",
                    "price_range": "$1,500 - $4,000",
                    "note": "Sculptural yet functional. The surface serves as a display platform for curated objects."
                },
                "premium": {
                    "product": "Crate & Barrel Liam Coffee Table or CB2 Plinth Table in oak",
                    "retailer": "Crate & Barrel / CB2",
                    "price_range": "$500 - $1,000",
                    "note": "Clean lines, storage shelf, and warm wood finish that complements the room's palette."
                },
                "budget": {
                    "product": "IKEA LACK or Target Project 62 square coffee table",
                    "retailer": "IKEA / Target",
                    "price_range": "$60 - $200",
                    "note": "Simple and functional. Style with a large tray, books, and a small plant."
                }
            },
            "recommended_tier": "premium"
        },
        "side_table": {
            "tiers": {
                "luxury": {
                    "product": "DWR Noguchi Table or RH Stone Accent Table",
                    "retailer": "Design Within Reach / Restoration Hardware",
                    "price_range": "$800 - $2,000",
                    "note": "A sculptural side table that stands alone as art. Choose a material that contrasts the sofa."
                },
                "premium": {
                    "product": "CB2 Acrylic or West Elm Metal Side Table",
                    "retailer": "CB2 / West Elm",
                    "price_range": "$200 - $400",
                    "note": "Transparent or slim metal profile keeps the room open. Adds function without visual weight."
                },
                "budget": {
                    "product": "IKEA LÖVBACKEN or VITTSJÖ nesting tables",
                    "retailer": "IKEA",
                    "price_range": "$30 - $80",
                    "note": "Nesting tables offer flexibility. Arrange as a pair for asymmetry."
                }
            },
            "recommended_tier": "budget"
        }
    }


def get_decor_recs(ctx):
    """Decor and accessory recommendations."""
    return {
        "throw_pillows": {
            "tiers": {
                "luxury": {
                    "product": "RH Belgian Linen Euro Sham set in ivory + accent toss in velvet",
                    "retailer": "Restoration Hardware",
                    "price_range": "$200 - $500",
                    "note": "European hem linen for an effortlessly rumpled look. Add one velvet toss in a jewel tone."
                },
                "premium": {
                    "product": "Pottery Barn faux fur + West Elm brushed cotton pillow set",
                    "retailer": "Pottery Barn / West Elm",
                    "price_range": "$60 - $150",
                    "note": "Mix two textures: one smooth cotton, one plush. Stick to 3 pillows for a curated look."
                },
                "budget": {
                    "product": "IKEA KARITANA + Target Threshold faux fur pillows",
                    "retailer": "IKEA / Target",
                    "price_range": "$15 - $40",
                    "note": "Inexpensive way to add color and texture. Use removable covers for easy seasonal swaps."
                }
            },
            "recommended_tier": "premium"
        },
        "wall_mirror": {
            "tiers": {
                "luxury": {
                    "product": "RH Versailles Arched Mirror or DWR Full Length Oval Mirror",
                    "retailer": "Restoration Hardware / Design Within Reach",
                    "price_range": "$1,000 - $3,000",
                    "note": "A mirror opposite a window doubles natural light and visually expands the room."
                },
                "premium": {
                    "product": "West Elm Arch Mirror or CB2 Sunburst Mirror",
                    "retailer": "West Elm / CB2",
                    "price_range": "$300 - $700",
                    "note": "Architectural shape that reads as art. Lean against the wall for an instant focal point."
                },
                "budget": {
                    "product": "IKEA HOVET or IKEA STAVE floor mirror",
                    "retailer": "IKEA",
                    "price_range": "$80 - $200",
                    "note": "Large-scale presence at a fraction of the cost. The simple frame won't compete with artwork."
                }
            },
            "recommended_tier": "budget"
        },
        "coffee_table_books": {
            "tiers": {
                "luxury": {
                    "product": "Taschen 'Interior Design' + Assouline 'Homes' series",
                    "retailer": "Assouline / Taschen",
                    "price_range": "$100 - $300",
                    "note": "Large-format art and design books that signal taste. Stack of 3 in graduated sizes."
                },
                "premium": {
                    "product": "Vox 'The Art of Living' + 'Cabins' by Gestalten",
                    "retailer": "Amazon / local bookstore",
                    "price_range": "$40 - $100",
                    "note": "Curated coffee table books with high production value. Focus on architecture or interiors."
                },
                "budget": {
                    "product": "Secondhand Taschen + design magazines from independent publishers",
                    "retailer": "eBay / thrift stores",
                    "price_range": "$10 - $40",
                    "note": "Mix hardcovers with a few current design magazines for a collected-over-time look."
                }
            },
            "recommended_tier": "premium"
        }
    }


def generate_shopping_guide(ctx, quiet=False):
    """Complete Step 4: generate the full shopping guide."""
    if not quiet:
        print(f"\nGalerie Noire — Shopping Guide Engine (Step 4)")
        print(f"Room: {ctx['room_type']} ({ctx['architecture_style']})")
        print("=" * 50)
    
    if not quiet:
        print("\n[1/4] Curating seating options...")
    seating = get_seating_recs(ctx)
    
    if not quiet:
        print("[2/4] Curating lighting options...")
    lighting = get_lighting_recs(ctx)
    
    if not quiet:
        print("[3/4] Curating rugs and tables...")
    rugs = get_rug_recs(ctx)
    tables = get_table_recs(ctx)
    
    if not quiet:
        print("[4/4] Curating decor accessories...")
    decor = get_decor_recs(ctx)
    
    # Select recommended tier based on room characteristics
    overall_tier = "premium"  # default for Galerie Noire's target client
    
    shopping_guide = {
        "retailer_overview": RETAILERS,
        "recommended_overall_tier": overall_tier,
        "seating": seating,
        "lighting": lighting,
        "rugs": rugs,
        "tables": tables,
        "decor": decor,
        "shopping_philosophy": (
            f"For this {ctx['room_type']}, invest in the sofa and lighting (where quality matters most), "
            f"save on side tables and accessories (where style can be found at any price). "
            f"{'Budget tier recommendations are included for clients who want a staged approach.' if overall_tier != 'luxury' else ''} "
            f"Note: Product recommendations are style-compatible suggestions based on the room's detected character. "
            f"Specific materials, finishes, and brands present in the room cannot be confirmed from the photo alone — "
            f"verify against actual room details before purchasing."
        ),
        "budget_allocation_guide": {
            "sofa": "35% of total budget",
            "lighting": "20%",
            "rug": "15%",
            "tables": "15%",
            "decor_accessories": "10%",
            "art_framing": "5%"
        },
        "retailer_focus": []
    }
    
    # Gather all recommended products across tiers
    products = []
    for category_name, category_data in [
        ("seating > sofa", seating["sofa"]),
        ("seating > chairs", seating["accent_chairs"]),
        ("lighting > floor", lighting["floor_lamp"]),
        ("lighting > picture", lighting["picture_light"]),
        ("lighting > table", lighting["table_lamp"]),
        ("rugs", rugs["area_rug"]),
        ("tables > coffee", tables["coffee_table"]),
        ("tables > side", tables["side_table"]),
    ]:
        rec_tier = category_data.get("recommended_tier", "premium")
        products.append({
            "category": category_name,
            "recommended_tier": rec_tier,
            "recommended_product": category_data["tiers"][rec_tier]["product"],
            "retailer": category_data["tiers"][rec_tier]["retailer"],
            "price_range": category_data["tiers"][rec_tier]["price_range"]
        })
    
    shopping_guide["product_summary"] = products
    
    return shopping_guide


# ─── Main Pipeline ──────────���─────────────────────────────────────────────────

def generate_guides(room_profile_path, output_dir=None, quiet=False):
    """
    Run both Step 3 (Styling Guide) and Step 4 (Shopping Guide).
    """
    if not quiet:
        print("=" * 60)
        print("Galerie Noire — Styling & Shopping Guide Engine")
        print(f"Loading room profile: {room_profile_path}")
        print("=" * 60)
    
    profile = load_room_profile(room_profile_path)
    ctx = extract_context(profile)
    
    if not quiet:
        print(f"Room: {ctx['room_type']} ({ctx['architecture_style']})")
        print()
    
    # Step 3
    styling_guide = generate_styling_guide(ctx, quiet=quiet)
    
    # Step 4
    shopping_guide = generate_shopping_guide(ctx, quiet=quiet)
    
    # Compile
    output = {
        "room_type": ctx["room_type"],
        "architecture_style": ctx["architecture_style"],
        "styling_guide": styling_guide,
        "shopping_guide": shopping_guide,
        "metadata": {
            "engine_version": "3.0.0",
            "pipeline_steps": [3, 4],
            "source_profile": str(room_profile_path)
        }
    }
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        out_path = output_dir / "styling_and_shopping_guide.json"
        with open(out_path, 'w') as f:
            json.dump(output, f, indent=2)
        if not quiet:
            print(f"\nSaved guides to: {out_path}")
    
    return output


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python styling_shopping_guide.py <room_profile.json> [--output-dir <dir>] [--json]")
        print()
        print("Generates Styling Guide (Step 3) and Shopping Guide (Step 4).")
        sys.exit(1)
    
    profile_path = sys.argv[1]
    output_dir = None
    quiet = "--json" in sys.argv
    
    if "--output-dir" in sys.argv:
        idx = sys.argv.index("--output-dir")
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]
    
    result = generate_guides(profile_path, output_dir=output_dir, quiet=quiet)
    
    if quiet:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 60)
        print("COMPLETE STYLING & SHOPPING GUIDE (JSON)")
        print("=" * 60)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()