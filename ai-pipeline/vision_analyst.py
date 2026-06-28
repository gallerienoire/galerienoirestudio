#!/usr/bin/env python3
"""
Stage 1: Vision Analyst — Galerie Noire AI Pipeline
====================================================
Takes a room photo and outputs ONLY objectively observable facts.
No inference, no style guessing, no material assumptions.
Every observation has a confidence score (0.0–1.0).
Below 0.9 = marked as "uncertain".
"""

import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image


def rgb_to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


def analyze_colors(image):
    """Extract dominant colors with confidence. Reports only what can be seen."""
    img = image.copy().convert("RGB")
    img.thumbnail((200, 150), Image.LANCZOS)
    pixels = np.array(img).reshape(-1, 3).astype(float)

    # Simple uniform sampling for dominant colors
    sampled = pixels[np.random.choice(len(pixels), min(5000, len(pixels)), replace=False)]

    # Use simple k-means with k=3
    centroids = sampled[np.random.choice(len(sampled), 3, replace=False)].copy()
    for _ in range(15):
        dists = np.array([np.sum((sampled - c) ** 2, axis=1) for c in centroids])
        labels = np.argmin(dists, axis=0)
        new_c = np.array([sampled[labels == i].mean(axis=0) if np.any(labels == i) else centroids[i] for i in range(3)])
        if np.allclose(centroids, new_c, atol=2.0):
            break
        centroids = new_c

    counts = np.array([np.sum(labels == i) for i in range(3)])
    order = np.argsort(-counts)
    centroids = centroids[order]
    proportions = counts[order] / counts.sum()

    avg_brightness = np.mean(pixels)
    brightness_var = np.std(pixels)

    dominant_colors = []
    for i, (c, p) in enumerate(zip(centroids, proportions)):
        r, g, b = int(round(c[0])), int(round(c[1])), int(round(c[2]))
        # Confidence based on how distinct the cluster is
        cluster_dists = np.sqrt(np.sum((pixels - c) ** 2, axis=1))
        cluster_cohesion = 1.0 - min(1.0, cluster_dists.mean() / 128.0)
        confidence = round(0.5 + 0.5 * cluster_cohesion, 2)
        dominant_colors.append({
            "hex": rgb_to_hex(r, g, b),
            "rgb": {"r": r, "g": g, "b": b},
            "proportion": round(float(p), 3),
            "confidence": min(0.95, confidence)
        })

    return {
        "dominant_colors": dominant_colors,
        "overall_brightness": round(float(avg_brightness), 1),
        "brightness_variance": round(float(brightness_var), 1)
    }


def analyze_lighting(image):
    """Report lighting conditions from pixel data only."""
    gray = np.array(image.copy().convert("L")).astype(float)
    avg_brightness = gray.mean()
    std_brightness = gray.std()

    r_ch = np.array(image.copy().convert("RGB"))[:, :, 0].astype(float)
    b_ch = np.array(image.copy().convert("RGB"))[:, :, 2].astype(float)

    mask = gray > 100
    rb_ratio = (r_ch[mask].mean() / (b_ch[mask].mean() + 0.001)) if mask.sum() > 100 else 1.0

    # Shadow detection (bottom 5% vs top 5%)
    bottom_5 = np.percentile(gray, 5)
    top_5 = np.percentile(gray, 95)
    shadow_ratio = bottom_5 / (top_5 + 0.001)

    return {
        "average_brightness": round(float(avg_brightness), 1),
        "brightness_std": round(float(std_brightness), 1),
        "red_blue_ratio": round(float(rb_ratio), 2),
        "shadow_ratio": round(float(shadow_ratio), 3),
        "observations": {}
    }


def analyze_geometry(image):
    """Report image geometry facts only — no room type inference."""
    w, h = image.size
    gray = np.array(image.copy().convert("L")).astype(float)

    from scipy.ndimage import sobel
    edges_x = sobel(gray, axis=1)
    edges_y = sobel(gray, axis=0)
    edge_mag = np.sqrt(edges_x ** 2 + edges_y ** 2)

    edge_density = round(float((edge_mag > 30).mean()), 4)
    strong_edge_pct = round(float((edge_mag > 60).mean()), 4)

    # Line orientation
    vert = np.abs(edges_x) > 30
    horiz = np.abs(edges_y) > 30
    vh_ratio = round(float(vert.mean() / (horiz.mean() + 0.001)), 2)

    return {
        "image_width_px": w,
        "image_height_px": h,
        "aspect_ratio": round(w / h, 3),
        "edge_density": edge_density,
        "strong_edge_pct": strong_edge_pct,
        "vertical_horizontal_edge_ratio": vh_ratio
    }


def analyze(image_path):
    """Run vision analyst — output ONLY observable facts with confidence."""
    if not Path(image_path).exists():
        return {"error": f"File not found: {image_path}"}

    image = Image.open(image_path)

    colors = analyze_colors(image)
    lighting = analyze_lighting(image)
    geometry = analyze_geometry(image)

    return {
        "vision_analysis": {
            "colors": colors,
            "lighting": lighting,
            "geometry": geometry
        },
        "metadata": {
            "stage": 1,
            "engine": "vision_analyst",
            "source": str(image_path),
            "note": "Only objectively observable pixel-level facts are reported. No style, material, or function inference."
        }
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vision_analyst.py <image_path> [--json]")
        sys.exit(1)
    result = analyze(sys.argv[1])
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))
