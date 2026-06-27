#!/usr/bin/env python3
"""
Room Analysis Engine — Galerie Noire AI Pipeline (Step 1)
=========================================================
Analyzes uploaded room photos and outputs a structured room profile (JSON).
Covers: architecture style, lighting conditions, color palette extraction,
furniture detection, wall space dimensions, viewing distance estimation.

The output feels like a professional interior designer's room assessment —
defensible, specific to this room, not templated.
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image


# ─── Color Analysis ───────────────────────────────────────────────────────────

def rgb_to_hex(r, g, b):
    """Convert RGB tuple to hex color string."""
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_hsl(r, g, b):
    """Convert RGB to HSL."""
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    cmax = max(r_norm, g_norm, b_norm)
    cmin = min(r_norm, g_norm, b_norm)
    delta = cmax - cmin

    # Lightness
    l = (cmax + cmin) / 2.0

    if delta == 0:
        h = s = 0.0
    else:
        # Saturation
        s = delta / (1.0 - abs(2.0 * l - 1.0))

        # Hue
        if cmax == r_norm:
            h = 60.0 * (((g_norm - b_norm) / delta) % 6)
        elif cmax == g_norm:
            h = 60.0 * (((b_norm - r_norm) / delta) + 2)
        else:
            h = 60.0 * (((r_norm - g_norm) / delta) + 4)

    return h, s, l


def kmeans_colors(pixels, k=5, max_iterations=20):
    """
    Manual K-means clustering for dominant color extraction.
    More memory-efficient than scikit-learn for image data.
    """
    # Sub-sample if too many pixels
    if len(pixels) > 100000:
        idx = np.random.choice(len(pixels), 100000, replace=False)
        pixels = pixels[idx]

    # Initialize centroids with k-means++ style
    centroids = []
    centroids.append(pixels[np.random.randint(len(pixels))])
    for _ in range(1, k):
        distances = np.min([
            np.sum((pixels - c.astype(float)) ** 2, axis=1)
            for c in centroids
        ], axis=0)
        probs = distances / distances.sum()
        centroids.append(pixels[np.random.choice(len(pixels), p=probs)])

    centroids = np.array(centroids, dtype=float)

    for _ in range(max_iterations):
        # Assign clusters
        distances = np.array([
            np.sum((pixels - c) ** 2, axis=1)
            for c in centroids
        ])
        labels = np.argmin(distances, axis=0)

        # Update centroids
        new_centroids = np.array([
            pixels[labels == i].mean(axis=0) if np.any(labels == i)
            else centroids[i]
            for i in range(k)
        ])

        if np.allclose(centroids, new_centroids, atol=1.0):
            break
        centroids = new_centroids

    # Count pixels per cluster
    counts = np.array([np.sum(labels == i) for i in range(k)])
    total = counts.sum()
    proportions = counts / total

    # Sort by proportion (most dominant first)
    order = np.argsort(-proportions)
    centroids = centroids[order]
    proportions = proportions[order]

    return centroids, proportions


def extract_color_palette(image):
    """
    Extract dominant and accent colors from the image.
    Returns structured color analysis.
    """
    img = image.copy()
    # Downsample for speed
    img.thumbnail((400, 300), Image.LANCZOS)
    pixels = np.array(img.convert("RGB"))
    h, w, _ = pixels.shape
    pixel_data = pixels.reshape(-1, 3).astype(float)

    # Extract dominant colors via K-means
    centroids, proportions = kmeans_colors(pixel_data, k=5)

    dominant_colors = []
    for i, (centroid, prop) in enumerate(zip(centroids, proportions)):
        r, g, b = int(round(centroid[0])), int(round(centroid[1])), int(round(centroid[2]))
        h_val, s, l = rgb_to_hsl(r, g, b)
        dominant_colors.append({
            "hex": rgb_to_hex(r, g, b),
            "rgb": {"r": r, "g": g, "b": b},
            "hsl": {"h": round(h_val, 1), "s": round(s, 3), "l": round(l, 3)},
            "proportion": round(float(prop), 3),
            "role": "dominant" if i == 0 else ("accent" if i < 3 else "tertiary")
        })

    # Determine color scheme type
    avg_hue = np.mean([c["hsl"]["h"] for c in dominant_colors[:3]])
    color_temp = "warm" if 0 <= avg_hue <= 60 or 300 <= avg_hue <= 360 else \
                 "cool" if 180 <= avg_hue <= 270 else "neutral"
    
    saturation_values = [c["hsl"]["s"] for c in dominant_colors[:3]]
    avg_saturation = np.mean(saturation_values)
    
    if avg_saturation < 0.15:
        scheme_type = "monochromatic"
    elif avg_saturation < 0.4:
        scheme_type = "muted"
    else:
        scheme_type = "vibrant"

    # Color harmony assessment
    hue_1 = dominant_colors[0]["hsl"]["h"] if len(dominant_colors) > 0 else 0
    hue_2 = dominant_colors[1]["hsl"]["h"] if len(dominant_colors) > 1 else 0
    hue_diff = abs(hue_1 - hue_2)
    
    if 30 <= hue_diff <= 60:
        harmony = "analogous"
    elif 120 <= hue_diff <= 180:
        harmony = "complementary"
    elif 85 <= hue_diff <= 115:
        harmony = "split-complementary"
    else:
        harmony = "mixed"

    return {
        "dominant_colors": dominant_colors,
        "color_scheme_type": scheme_type,
        "color_temperature": color_temp,
        "harmony": harmony,
        "warmth_score": round(float(avg_hue / 360.0), 3) if avg_hue else 0.5,
        "vibrancy": "high" if avg_saturation > 0.5 else ("medium" if avg_saturation > 0.25 else "low")
    }


# ─── Lighting Analysis ────────────────────────────────────────────────────────

def analyze_lighting(image):
    """
    Analyze lighting conditions from the image:
    - Overall brightness
    - Color temperature (warm/cool)
    - Light source detection
    - Shadow severity
    """
    img = image.copy()
    img.thumbnail((400, 300), Image.LANCZOS)
    pixels = np.array(img.convert("RGB"))
    
    # Convert to grayscale for brightness analysis
    gray = np.array(img.convert("L")).astype(float)
    
    # Overall brightness (0-255)
    avg_brightness = gray.mean()
    brightness_level = "very_dark" if avg_brightness < 50 else \
                       "dark" if avg_brightness < 100 else \
                       "moderate" if avg_brightness < 150 else \
                       "bright" if avg_brightness < 200 else \
                       "very_bright"
    
    # Brightness distribution (variance = contrast)
    brightness_std = gray.std()
    contrast = "low" if brightness_std < 30 else \
               "medium" if brightness_std < 60 else \
               "high"
    
    # Estimate color temperature from white balance
    r_channel = pixels[:, :, 0].astype(float)
    b_channel = pixels[:, :, 2].astype(float)
    
    # Red/blue ratio in bright areas
    mask = gray > 150
    if mask.sum() > 100:
        r_avg = r_channel[mask].mean()
        b_avg = b_channel[mask].mean()
        rb_ratio = r_avg / (b_avg + 0.001)
    else:
        rb_ratio = 1.0
    
    if rb_ratio > 1.2:
        color_temp = "warm"  # Incandescent, sunset
    elif rb_ratio < 0.85:
        color_temp = "cool"  # Fluorescent, overcast
    else:
        color_temp = "neutral"  # Daylight balanced

    # Shadow detection (dark regions in an otherwise bright scene)
    # Darkest 10% percentile brightness
    bottom_10 = np.percentile(gray, 10)
    top_10 = np.percentile(gray, 90)
    shadow_ratio = bottom_10 / (top_10 + 0.001)
    
    shadow_severity = "heavy" if shadow_ratio < 0.15 else \
                      "moderate" if shadow_ratio < 0.35 else \
                      "minimal"

    # Estimate number of light sources by looking for gradient directions
    # Simple approach: horizontal and vertical gradient variance
    h_grad = np.abs(np.diff(gray, axis=1))
    v_grad = np.abs(np.diff(gray, axis=0))
    
    gradient_strength = (h_grad.mean() + v_grad.mean()) / 2.0
    lighting_evenness = "even" if gradient_strength < 15 else \
                        "directional" if gradient_strength < 35 else \
                        "dramatic"

    return {
        "overall_brightness": round(float(avg_brightness), 1),
        "brightness_level": brightness_level,
        "contrast": contrast,
        "color_temperature": color_temp,
        "rb_ratio": round(float(rb_ratio), 2),
        "shadow_severity": shadow_severity,
        "lighting_evenness": lighting_evenness,
        "mood": "cozy_soft" if brightness_level in ("dark", "very_dark") and color_temp == "warm" else
                "bright_crisp" if brightness_level in ("bright", "very_bright") and color_temp == "neutral" else
                "clinical" if brightness_level in ("bright", "very_bright") and color_temp == "cool" else
                "dramatic" if contrast == "high" and shadow_severity in ("moderate", "heavy") else
                "natural_even" if lighting_evenness == "even" and color_temp == "neutral" else
                "mixed_ambient"
    }


# ─── Architecture & Dimensions ────────────────────────────────────────────────

def estimate_room_dimensions(image):
    """
    Estimate room dimensions from image.
    Uses perspective cues, known reference points, and image geometry.
    """
    img = image.copy()
    w, h = img.size
    
    aspect_ratio = w / h
    
    # Room type guess based on aspect ratio and common interior photography
    # Standard room photos: living rooms ~4:3 (1.33), bedrooms/dining ~3:2 (1.5)
    # Wide shots (>1.6) tend to be open-plan or panoramic
    # Almost square (<1.1) tend to be close-ups or detail shots
    if aspect_ratio > 1.7:
        room_type_guess = "open_plan_or_panoramic"
    elif aspect_ratio > 1.4:
        room_type_guess = "living_room"
    elif aspect_ratio > 1.15:
        room_type_guess = "bedroom_or_dining"
    elif aspect_ratio > 1.0:
        room_type_guess = "study_or_small_room"
    else:
        room_type_guess = "close_up_or_detail_shot"

    # Estimate ceiling height based on image proportions
    # Typical interior photos: ceiling is roughly 20-30% of image height
    gray = np.array(img.convert("L"))
    
    # Find horizontal lines (potential ceiling-wall or floor-wall boundaries)
    # by looking at horizontal gradient peaks
    h_grad = np.abs(np.diff(gray.astype(float), axis=1))
    row_gradients = h_grad.mean(axis=1)
    
    # Smooth and find peaks
    from scipy.ndimage import gaussian_filter1d
    smoothed = gaussian_filter1d(row_gradients, sigma=3)
    
    # Find top and bottom strong horizontal edges
    top_third = smoothed[:h//3]
    bottom_third = smoothed[2*h//3:]
    
    ceiling_line_y = np.argmax(top_third) if top_third.max() > gray.mean() * 0.3 else h * 0.08
    floor_line_y = h - np.argmax(bottom_third[::-1]) if bottom_third.max() > gray.mean() * 0.3 else h * 0.92
    
    visible_wall_height = floor_line_y - ceiling_line_y
    # Normalize: visible wall as fraction of image height, then scale to realistic room height
    wall_fraction = visible_wall_height / h
    # In a typical interior photo, the wall occupies ~60-75% of the vertical space
    # Map wall_fraction to ceiling height in a realistic 2.4m-3.6m range
    # 0.6 fraction -> ~2.5m ceiling (standard), 0.75 fraction -> ~3.0m (generous)
    ceiling_height_m = round(2.1 + wall_fraction * 1.5, 1)
    ceiling_height_m = min(3.6, max(2.2, ceiling_height_m))  # clamp to realistic range
    
    if ceiling_height_m > 3.2:
        ceiling_cat = "cathedral_or_high"
    elif ceiling_height_m > 2.8:
        ceiling_cat = "standard_plus"
    elif ceiling_height_m > 2.4:
        ceiling_cat = "standard"
    else:
        ceiling_cat = "low"

    return {
        "image_dimensions_px": {"width": w, "height": h},
        "aspect_ratio": round(aspect_ratio, 2),
        "room_type_guess": room_type_guess,
        "ceiling_height_estimate_m": ceiling_height_m,
        "ceiling_category": ceiling_cat,
        "confidence": "estimate"  # placeholder for when ML models are integrated
    }


# ─── Architecture Style Detection ─────────────────────────────────────────────

def detect_architecture_style(image, color_profile, lighting):
    """
    Detect architectural style based on visual cues.
    Uses color palettes, lighting patterns, and geometric analysis.
    """
    img = image.copy()
    img.thumbnail((400, 300), Image.LANCZOS)
    gray = np.array(img.convert("L")).astype(float)
    pixels = np.array(img.convert("RGB")).astype(float)
    h, w = pixels.shape[:2]
    
    # Edge analysis for architectural style
    from scipy.ndimage import sobel
    
    edges_x = sobel(gray, axis=1)
    edges_y = sobel(gray, axis=0)
    edge_magnitude = np.sqrt(edges_x**2 + edges_y**2)
    
    edge_density = (edge_magnitude > 30).mean()
    
    # Line orientation analysis
    # Vertical edges suggest columns, tall windows, modern lines
    # Horizontal edges suggest moldings, beams, traditional architecture
    strong_edges_x = np.abs(edges_x) > 30
    strong_edges_y = np.abs(edges_y) > 30
    
    vertical_density = strong_edges_x.mean()
    horizontal_density = strong_edges_y.mean()
    
    # Calculate ratio of vertical to horizontal lines
    vh_ratio = vertical_density / (horizontal_density + 0.001)
    
    # Texture analysis
    texture_variance = gray.std()
    
    # Warmth and material estimation
    r_avg = pixels[:, :, 0].mean()
    b_avg = pixels[:, :, 2].mean()
    warmth_index = (r_avg - b_avg) / 255.0

    # Style classification based on combined cues
    scores = {}
    
    # Mid-century Modern: warm wood tones, clean horizontal lines, open feel
    scores["mid_century_modern"] = (
        (0.3 if 0.05 < warmth_index < 0.2 else 0.1) +
        (0.3 if 0.8 < vh_ratio < 1.5 else 0.1) +
        (0.2 if lighting["lighting_evenness"] == "even" else 0.1) +
        (0.2 if edge_density < 0.15 else 0.05)
    )
    
    # Contemporary/Modern: clean lines, neutral palette, high contrast
    scores["contemporary_modern"] = (
        (0.3 if color_profile["color_temperature"] in ("cool", "neutral") else 0.05) +
        (0.3 if vh_ratio > 1.2 else 0.1) +
        (0.2 if lighting["contrast"] in ("medium", "high") else 0.1) +
        (0.2 if texture_variance < 50 else 0.05)
    )
    
    # Traditional/Classic: warm tones, decorative elements, more horizontal
    scores["traditional_classic"] = (
        (0.3 if warmth_index > 0.12 else 0.05) +
        (0.3 if vh_ratio < 0.8 else 0.1) +
        (0.2 if lighting["lighting_evenness"] == "directional" else 0.05) +
        (0.2 if edge_density > 0.15 else 0.05)
    )
    
    # Industrial: cool tones, high contrast, strong architectural lines
    scores["industrial_loft"] = (
        (0.3 if color_profile["color_temperature"] == "cool" else 0.05) +
        (0.3 if lighting["contrast"] == "high" else 0.1) +
        (0.2 if edge_density > 0.2 else 0.05) +
        (0.2 if texture_variance > 65 else 0.05)
    )
    
    # Scandinavian: bright, minimal, clean, warm-neutral
    scores["scandinavian"] = (
        (0.3 if lighting["brightness_level"] in ("bright", "very_bright") else 0.05) +
        (0.3 if color_profile["color_temperature"] == "warm" else 0.05) +
        (0.2 if edge_density < 0.1 else 0.1) +
        (0.2 if color_profile["vibrancy"] == "low" else 0.1)
    )
    
    # Bohemian/Eclectic: vibrant colors, mixed textures, warm
    scores["bohemian_eclectic"] = (
        (0.3 if color_profile["vibrancy"] in ("medium", "high") else 0.05) +
        (0.3 if color_profile["harmony"] == "mixed" else 0.1) +
        (0.2 if warmth_index > 0.1 else 0.1) +
        (0.2 if texture_variance > 55 else 0.1)
    )

    # Farmhouse/Rustic: warm, textured, natural materials
    scores["farmhouse_rustic"] = (
        (0.3 if warmth_index > 0.15 else 0.05) +
        (0.3 if texture_variance > 55 else 0.1) +
        (0.2 if color_profile["vibrancy"] == "low" else 0.1) +
        (0.2 if lighting["mood"] == "cozy_soft" else 0.05)
    )

    # Find best matching style
    best_style = max(scores, key=scores.get)
    best_score = scores[best_style]
    
    # Calculate confidence
    if best_score > 0.7:
        confidence = "high"
    elif best_score > 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "primary_style": best_style.replace("_", " ").title(),
        "style_scores": {k.replace("_", " ").title(): round(v, 2) for k, v in 
                        sorted(scores.items(), key=lambda x: -x[1])},
        "confidence": confidence,
        "style_characteristics": {
            "edge_density": round(float(edge_density), 3),
            "vertical_horizontal_ratio": round(float(vh_ratio), 2),
            "texture_variance": round(float(texture_variance), 1),
            "warmth_index": round(float(warmth_index), 3)
        }
    }


# ─── Furniture Detection ──────────────────────────────────────────────────────

def detect_furniture(image):
    """
    Detect and classify furniture from the image.
    Uses color segmentation, edge detection, and spatial analysis.
    """
    img = image.copy()
    img.thumbnail((400, 300), Image.LANCZOS)
    pixels = np.array(img.convert("RGB")).astype(float)
    gray = np.array(img.convert("L")).astype(float)
    h, w = pixels.shape[:2]
    
    from scipy.ndimage import sobel
    
    edges_x = sobel(gray, axis=1)
    edges_y = sobel(gray, axis=0)
    edge_mag = np.sqrt(edges_x**2 + edges_y**2)
    
    # Furniture presence score - look for clusters of edges in lower portion
    bottom_half = edge_mag[h//2:, :]
    bottom_edge_density = (bottom_half > 25).mean()
    
    # Furniture coverage estimate
    furniture_coverage = min(0.8, bottom_edge_density * 2.5)
    
    # Check for distinct color regions that suggest furniture
    # Segment by color similarity using simple thresholding
    # Look for large contiguous regions of similar color
    
    # Rough segmentation: divide image into grid and check color variance
    grid_size = 8
    cell_h, cell_w = h // grid_size, w // grid_size
    color_variances = []
    
    for i in range(grid_size):
        for j in range(grid_size):
            y1, y2 = i * cell_h, (i + 1) * cell_h
            x1, x2 = j * cell_w, (j + 1) * cell_w
            cell = pixels[y1:y2, x1:x2]
            color_variances.append(cell.std(axis=(0, 1)).mean())
    
    avg_color_variance = np.mean(color_variances)
    
    # Low variance regions in lower half suggest furniture surfaces
    lower_variances = []
    for i in range(grid_size // 2, grid_size):
        for j in range(grid_size):
            y1, y2 = i * cell_h, (i + 1) * cell_h
            x1, x2 = j * cell_w, (j + 1) * cell_w
            cell = pixels[y1:y2, x1:x2]
            lower_variances.append(cell.std(axis=(0, 1)).mean())
    
    lower_avg_variance = np.mean(lower_variances)
    furniture_surface_quality = "smooth_unified" if lower_avg_variance < avg_color_variance * 0.8 else "varied_textured"

    # Estimate furniture items count from edge clusters
    # (Simplified — full detection requires object detection model)
    # Count connected components in the edge image
    from scipy.ndimage import label
    
    edge_binary = edge_mag > 30
    labeled, num_features = label(edge_binary)
    
    # Filter tiny components
    unique, counts = np.unique(labeled[labeled > 0], return_counts=True)
    significant_components = sum(1 for c in counts if c > 100)
    
    estimated_items = min(8, max(2, significant_components // 3))
    
    # Layout detection
    # Check if furniture is arranged against walls (perimeter) or in center
    center_region = pixels[h//4:3*h//4, w//4:3*w//4]
    center_edge_density = (sobel(np.array(Image.fromarray(
        center_region.astype(np.uint8)).convert("L")).astype(float), axis=1) > 25).mean()
    
    perimeter_region_top = pixels[:h//4, :]
    perimeter_region_bottom = pixels[3*h//4:, :]
    perimeter_region_left = pixels[:, :w//4]
    perimeter_region_right = pixels[:, 3*w//4:]
    
    # Simplified layout classification
    if furniture_coverage > 0.5 and center_edge_density > 0.1:
        layout = "conversation_seating"  # Furniture arranged for conversation
    elif furniture_coverage > 0.4:
        layout = "traditional_arrangement"  # Against walls
    else:
        layout = "minimal_sparse"

    return {
        "items_detected_count": estimated_items,
        "furniture_coverage": round(float(furniture_coverage), 2),
        "layout_style": layout,
        "furniture_surface": furniture_surface_quality,
        "furniture_style_guess": "modern_sleek" if furniture_surface_quality == "smooth_unified" else "traditional_textured",
        "confidence": "medium",
        "notes": "Full object detection requires ML model integration; this is a statistical estimate based on edge and color analysis."
    }


# ─── Wall Space & Artwork Recommendations ─────────────────────────────────────

def analyze_wall_space(image, room_profile):
    """
    Analyze available wall space and recommend optimal artwork dimensions.
    """
    img = image.copy()
    w, h = img.size
    gray = np.array(img.convert("L")).astype(float)
    
    from scipy.ndimage import sobel
    edges_x = sobel(gray, axis=1)
    edges_y = sobel(gray, axis=0)
    edge_mag = np.sqrt(edges_x**2 + edges_y**2)
    
    # Find largest clear wall regions (areas with low edge density)
    # Divide image into quadrants and score each for "wall-ness"
    quadrants = {
        "top_left": edge_mag[:h//2, :w//2],
        "top_right": edge_mag[:h//2, w//2:],
        "bottom_left": edge_mag[h//2:, :w//2],
        "bottom_right": edge_mag[h//2:, w//2:]
    }
    
    wall_scores = {}
    for name, region in quadrants.items():
        edge_density = (region > 25).mean()
        avg_brightness = gray[:h//2 if "top" in name else h//2, 
                              :w//2 if "left" in name else w//2].mean() if True else 0
        
        # A good wall for artwork: low edge density, medium brightness (not a window)
        score = (1.0 - edge_density) * 0.6 + (0.5 if 80 < avg_brightness < 200 else 0.2) * 0.4
        wall_scores[name] = round(float(score), 3)
    
    best_wall = max(wall_scores, key=wall_scores.get)
    
    # Estimate optimal artwork size based on wall space and viewing distance
    # Rule of thumb: artwork should be 50-75% of furniture width, 
    # or for empty walls, about 1/3 to 2/3 of wall width
    
    # Normalized wall dimensions (assuming standard room proportions)
    wall_width_m = 3.0 + (w / h) * 1.5  # estimate in meters
    wall_height_m = room_profile["architecture"]["ceiling_height_estimate_m"] * 0.7
    
    # Optimal artwork size (rule of thirds for wall)
    optimal_width_m = round(wall_width_m * 0.6, 1)
    optimal_height_m = round(wall_height_m * 0.65, 1)
    
    # Constrain to reasonable artwork sizes
    optimal_width_m = min(2.0, max(0.5, optimal_width_m))
    optimal_height_m = min(1.5, max(0.4, optimal_height_m))
    
    return {
        "available_walls": wall_scores,
        "primary_wall": best_wall,
        "wall_width_estimate_m": round(wall_width_m, 1),
        "wall_height_estimate_m": round(wall_height_m, 1),
        "recommended_artwork_width_cm": round(optimal_width_m * 100),
        "recommended_artwork_height_cm": round(optimal_height_m * 100),
        "recommended_aspect_ratio": round(optimal_width_m / optimal_height_m, 2),
        "notes": "Recommend 1 large statement piece or 3 smaller pieces in a triptych arrangement."
    }


# ─── Viewing Distance Estimation ──────────────────────────────────────────────

def estimate_viewing_distance(image, wall_analysis):
    """
    Estimate the typical viewing distance and optimal artwork size.
    """
    img = image.copy()
    w, h = img.size
    
    # In a typical room photo, the camera is usually positioned from a
    # natural viewing position (across the room, ~3-5 meters from main wall)
    
    # Estimate based on image field of view and room proportions
    # Standard interior photo FOV ~60-75 degrees
    
    # For a wall that fills ~60-80% of image width, viewing distance is ~1.5x wall width
    art_width_cm = wall_analysis["recommended_artwork_width_cm"]
    art_height_cm = wall_analysis["recommended_artwork_height_cm"]
    
    # Optimal viewing distance: 1.5-2x the diagonal of the artwork
    diagonal_cm = math.sqrt(art_width_cm**2 + art_height_cm**2)
    optimal_viewing_distance_m = round(diagonal_cm / 100 * 1.5, 1)
    
    # Typical room viewing distance (where the sofa/chair would be)
    typical_viewing_distance_m = round(optimal_viewing_distance_m * 1.2, 1)
    
    # Eye level (standard ~1.5m from floor)
    # Center of artwork should be at eye level
    
    # Optimal artwork height on wall
    art_center_height_m = 1.5  # eye level
    bottom_of_art_m = round(art_center_height_m - (art_height_cm / 200), 1)
    top_of_art_m = round(art_center_height_m + (art_height_cm / 200), 1)
    
    return {
        "optimal_viewing_distance_m": optimal_viewing_distance_m,
        "typical_viewing_distance_m": typical_viewing_distance_m,
        "artwork_center_height_m": art_center_height_m,
        "artwork_bottom_from_floor_m": max(0.6, bottom_of_art_m),
        "artwork_top_from_floor_m": top_of_art_m,
        "eye_level_height_m": 1.5,
        "recommended_frame_size": "large_statement" if art_width_cm > 120 else
                                   "medium" if art_width_cm > 75 else "small_accent"
    }


# ─── Main Pipeline ────────────────────────────────────────────────────────────

def analyze_room(image_path, quiet=False):
    """
    Main room analysis pipeline.
    Takes an image path and returns a complete structured room profile.
    
    Args:
        image_path: Path to the room photo
        quiet: If True, suppresses progress output (for API use)
    
    Returns dict with all analysis sections.
    """
    if not quiet:
        print(f"Galerie Noire — Room Analysis Engine")
        print(f"Analyzing: {image_path}", flush=True)
        print("=" * 50, flush=True)
    
    # Load image
    if not Path(image_path).exists():
        return {"error": f"File not found: {image_path}"}
    
    try:
        image = Image.open(image_path)
    except Exception as e:
        return {"error": f"Cannot open image: {e}"}
    
    if not quiet:
        print(f"Image: {image.size[0]}x{image.size[1]}px | Mode: {image.mode}")
    
    # Run all analysis modules
    if not quiet:
        print("\n[1/6] Extracting color palette...")
    color_profile = extract_color_palette(image)
    if not quiet:
        print(f"       Dominant: {color_profile['dominant_colors'][0]['hex']} | "
              f"Scheme: {color_profile['color_scheme_type']} ({color_profile['color_temperature']})")
    
    if not quiet:
        print("[2/6] Analyzing lighting...")
    lighting = analyze_lighting(image)
    if not quiet:
        print(f"       Brightness: {lighting['brightness_level']} | "
              f"Mood: {lighting['mood']} | Temp: {lighting['color_temperature']}")
    
    if not quiet:
        print("[3/6] Estimating room dimensions...")
    dimensions = estimate_room_dimensions(image)
    if not quiet:
        print(f"       Type: {dimensions['room_type_guess']} | "
              f"Ceiling: {dimensions['ceiling_height_estimate_m']}m")
    
    if not quiet:
        print("[4/6] Detecting architecture style...")
    architecture = detect_architecture_style(image, color_profile, lighting)
    if not quiet:
        print(f"       Style: {architecture['primary_style']} ({architecture['confidence']})")
    
    if not quiet:
        print("[5/6] Detecting furniture...")
    furniture = detect_furniture(image)
    if not quiet:
        print(f"       Items: ~{furniture['items_detected_count']} | "
              f"Coverage: {furniture['furniture_coverage']} | "
              f"Layout: {furniture['layout_style']}")
    
    if not quiet:
        print("[6/6] Analyzing wall space & viewing distance...")
    room_profile_base = {"architecture": dimensions}
    wall_analysis = analyze_wall_space(image, room_profile_base)
    viewing = estimate_viewing_distance(image, wall_analysis)
    if not quiet:
        print(f"       Best wall: {wall_analysis['primary_wall']} | "
              f"Art size: {wall_analysis['recommended_artwork_width_cm']}x"
              f"{wall_analysis['recommended_artwork_height_cm']}cm")
    
    # Compile full profile
    profile = {
        "room_profile": {
            "color_palette": color_profile,
            "lighting": lighting,
            "architecture": dimensions,
            "architecture_style": architecture,
            "furniture": furniture,
            "wall_space": wall_analysis,
            "viewing_distance": viewing
        },
        "metadata": {
            "engine_version": "1.0.0",
            "pipeline_step": 1,
            "analyzed_at": None,  # populated by caller if needed
            "source_image": str(image_path)
        }
    }
    
    return profile


def profile_to_json(profile):
    """Convert profile to pretty-printed JSON string."""
    return json.dumps(profile, indent=2)


# ─── CLI Entry Point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 room_analysis.py <image_path> [--json]")
        print()
        print("Analyzes a room photo and produces a structured room profile.")
        print("  --json    Output raw JSON only (no progress messages)")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_json = "--json" in sys.argv
    
    profile = analyze_room(image_path, quiet=output_json)
    
    if "error" in profile:
        print(f"ERROR: {profile['error']}", file=sys.stderr)
        sys.exit(1)
    
    if output_json:
        print(profile_to_json(profile))
    else:
        print("\n" + "=" * 50)
        print("COMPLETE ROOM PROFILE (JSON)")
        print("=" * 50)
        print(profile_to_json(profile))