# Galerie Noire — AI Pipeline: Room Analysis Engine (Step 1)

## Overview

This is Step 1 of the AI pipeline. It analyzes uploaded room photos and produces a structured room profile (JSON) that downstream steps consume:

- **Step 2 (Artwork Generation)**: Takes the room profile to generate 5 custom digital artworks
- **Step 3 (Styling Guide Generation)**: Takes the profile to recommend layout changes, frame styles, lighting
- **Step 4 (Shopping Guide Generation)**: Takes the profile to recommend furniture/decor items

## Usage

### Quick Start
```bash
cd /home/team/shared/ai-pipeline
./venv/bin/python room_analysis.py <image_path>
```

### Options
- `<image_path>` — Path to a JPEG/PNG room photo
- `--json` — Output raw JSON only (no progress messages). Use this for API integration.

### Examples
```bash
# Analyze with progress output
./venv/bin/python room_analysis.py test_room.jpg

# Get JSON-only output (for API consumption)
./venv/bin/python room_analysis.py test_room.jpg --json > room_profile.json
```

## Output Schema

The pipeline returns a JSON object with this structure:

```json
{
  "room_profile": {
    "color_palette": {
      "dominant_colors": [
        {
          "hex": "#ded2bf",
          "rgb": {"r": 222, "g": 210, "b": 191},
          "hsl": {"h": 36.8, "s": 0.32, "l": 0.81},
          "proportion": 0.431,
          "role": "dominant|accent|tertiary"
        }
      ],
      "color_scheme_type": "monochromatic|muted|vibrant",
      "color_temperature": "warm|cool|neutral",
      "harmony": "analogous|complementary|split-complementary|mixed",
      "warmth_score": 0.0-1.0,
      "vibrancy": "high|medium|low"
    },
    "lighting": {
      "overall_brightness": 0-255,
      "brightness_level": "very_dark|dark|moderate|bright|very_bright",
      "contrast": "low|medium|high",
      "color_temperature": "warm|cool|neutral",
      "rb_ratio": 0.0-2.0,
      "shadow_severity": "heavy|moderate|minimal",
      "lighting_evenness": "even|directional|dramatic",
      "mood": "cozy_soft|bright_crisp|clinical|dramatic|natural_even|mixed_ambient"
    },
    "architecture": {
      "image_dimensions_px": {"width": int, "height": int},
      "aspect_ratio": float,
      "room_type_guess": "living_room|bedroom_or_dining|study_or_small_room|...",
      "ceiling_height_estimate_m": float,
      "ceiling_category": "cathedral_or_high|standard_plus|standard|low",
      "confidence": "estimate"
    },
    "architecture_style": {
      "primary_style": "Mid-Century Modern|Contemporary Modern|...",
      "style_scores": {"Style Name": score},
      "confidence": "high|medium|low",
      "style_characteristics": {
        "edge_density": float,
        "vertical_horizontal_ratio": float,
        "texture_variance": float,
        "warmth_index": float
      }
    },
    "furniture": {
      "items_detected_count": int,
      "furniture_coverage": 0.0-1.0,
      "layout_style": "conversation_seating|traditional_arrangement|minimal_sparse",
      "furniture_surface": "smooth_unified|varied_textured",
      "furniture_style_guess": "modern_sleek|traditional_textured",
      "confidence": "medium",
      "notes": "string"
    },
    "wall_space": {
      "available_walls": {"top_left|top_right|bottom_left|bottom_right": score},
      "primary_wall": "best wall quadrant",
      "wall_width_estimate_m": float,
      "wall_height_estimate_m": float,
      "recommended_artwork_width_cm": int,
      "recommended_artwork_height_cm": int,
      "recommended_aspect_ratio": float,
      "notes": "string"
    },
    "viewing_distance": {
      "optimal_viewing_distance_m": float,
      "typical_viewing_distance_m": float,
      "artwork_center_height_m": 1.5,
      "artwork_bottom_from_floor_m": float,
      "artwork_top_from_floor_m": float,
      "eye_level_height_m": 1.5,
      "recommended_frame_size": "large_statement|medium|small_accent"
    }
  },
  "metadata": {
    "engine_version": "1.0.0",
    "pipeline_step": 1,
    "analyzed_at": null,
    "source_image": "path"
  }
}
```

## Architecture

The pipeline is organized into independent, composable modules:

| Module | Function | Description |
|--------|----------|-------------|
| Color Palette | `extract_color_palette()` | K-means clustering on image pixels → dominant colors, scheme type, harmony |
| Lighting | `analyze_lighting()` | Brightness, contrast, color temperature, shadow severity, mood |
| Dimensions | `estimate_room_dimensions()` | Room type guess, ceiling height estimate from image geometry |
| Architecture Style | `detect_architecture_style()` | Multi-factorial style classification (7 styles scored) |
| Furniture | `detect_furniture()` | Edge-based furniture detection, coverage, layout style |
| Wall Space | `analyze_wall_space()` | Wall quadrants scored, optimal artwork size recommendation |
| Viewing Distance | `estimate_viewing_distance()` | Optimal/typical viewing distance, eye-level placement |

## Dependencies

- Python 3.12+
- Pillow (image loading/manipulation)
- NumPy (numerical operations)
- SciPy (ndimage filters: sobel, gaussian_filter, label)

All in `venv/`. Activate with: `source venv/bin/activate`

## Extending

### Adding a new architecture style
1. Add a new scoring branch in `detect_architecture_style()`
2. Weight your style's visual cues (edge density, warmth, texture, etc.)
3. It will automatically appear in `style_scores` and the best-matching check

### Integrating ML models
The engine is designed to accept ML model predictions:
- Replace `kmeans_colors()` with a color-naming model (e.g., from CLIP)
- Replace `detect_furniture()` edge-based detection with YOLO/Detectron2
- Replace architecture style rules with a ResNet/EfficientNet classifier
- Each module has a `confidence` field for this purpose

## Testing

A synthetic test image is included:
```bash
./venv/bin/python room_analysis.py test_room.jpg
```

The test image simulates a living room with:
- Warm beige walls with crown molding
- Window on left wall (natural daylight)
- Modern grey sofa with accent pillows
- Mid-century coffee table
- Floor lamp (warm accent lighting)
- Area rug