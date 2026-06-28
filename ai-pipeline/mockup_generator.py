#!/usr/bin/env python3
"""
Room Mockup Generator — Galerie Noire AI Pipeline
==================================================
Takes the actual uploaded room photo and composites artwork onto the detected
best wall location. Uses the room profile JSON to position artwork correctly
in the actual room perspective.

Usage:
    python mockup_generator.py <room_photo.jpg> <room_profile.json> <artwork_dir> [--output <path>]

The artwork_dir should contain the generated artwork PNGs named artwork-1.png through artwork-5.png.
Output is saved as a composite image showing how the artwork looks in the actual room.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


def load_room_profile(profile_path):
    """Load room analysis JSON."""
    with open(profile_path) as f:
        return json.load(f)


def find_best_wall(profile, img_w, img_h):
    """
    Determine the best wall quadrant for artwork placement using room analysis.
    Returns (center_x, center_y, width, height, rotation_angle) for the artwork
    placement region in image pixel coordinates.
    """
    rp = profile.get("room_profile", profile)
    walls = rp.get("wall_space", {})
    viewing = rp.get("viewing_distance", {})

    primary_wall = walls.get("primary_wall", "top_right")

    # Map wall quadrant to image region
    quadrants = {
        "top_left":      (img_w // 4, img_h // 4, img_w // 2, img_h // 2),
        "top_right":     (3 * img_w // 4, img_h // 4, img_w // 2, img_h // 2),
        "bottom_left":   (img_w // 4, 3 * img_h // 4, img_w // 2, img_h // 2),
        "bottom_right":  (3 * img_w // 4, 3 * img_h // 4, img_w // 2, img_h // 2),
    }

    if primary_wall in quadrants:
        cx, cy, pw, ph = quadrants[primary_wall]
    else:
        # Default to upper center
        cx, cy, pw, ph = img_w // 2, img_h // 3, img_w // 2, img_h // 2

    # Artwork dimensions from room analysis (cm) → scale to image pixels
    art_w_cm = walls.get("recommended_artwork_width_cm", 120)
    art_h_cm = walls.get("recommended_artwork_height_cm", 90)
    aspect = art_w_cm / max(art_h_cm, 1)

    # Scale artwork to fit ~60% of the wall region
    max_art_w = int(pw * 0.6)
    max_art_h = int(ph * 0.6)

    if aspect > max_art_w / max_art_h:
        art_px_w = max_art_w
        art_px_h = int(max_art_w / aspect)
    else:
        art_px_h = max_art_h
        art_px_w = int(max_art_h * aspect)

    art_px_w = max(50, min(art_px_w, int(img_w * 0.7)))
    art_px_h = max(50, min(art_px_h, int(img_h * 0.5)))

    # Apply slight perspective rotation based on wall quadrant
    angle_map = {
        "top_left": 2,
        "top_right": -2,
        "bottom_left": 1,
        "bottom_right": -1,
    }
    angle = angle_map.get(primary_wall, 0)

    return {
        "center_x": cx,
        "center_y": cy,
        "artwork_width_px": art_px_w,
        "artwork_height_px": art_px_h,
        "rotation_angle": angle,
        "wall_quadrant": primary_wall
    }


def create_mockup(room_image_path, room_profile_path, artwork_dir, output_path=None):
    """
    Create a mockup by overlaying artwork onto the actual room photo.
    Steps:
    1. Load and analyze the room photo
    2. Find the best wall placement using room profile
    3. Load generated artwork images
    4. Composite artwork onto the room photo with perspective and shadow
    5. Save the result
    """
    # Load room photo
    room = Image.open(room_image_path).convert("RGB")
    img_w, img_h = room.size

    # Load room profile
    profile = load_room_profile(room_profile_path)

    # Find placement
    placement = find_best_wall(profile, img_w, img_h)
    cx, cy = placement["center_x"], placement["center_y"]
    aw, ah = placement["artwork_width_px"], placement["artwork_height_px"]
    angle = placement["rotation_angle"]

    # Find artwork images
    artwork_dir = Path(artwork_dir)
    artwork_files = sorted([
        str(p) for p in artwork_dir.glob("*.png")
        if p.stem.startswith("artwork")
    ])

    if not artwork_files:
        # Also check for any png
        artwork_files = sorted([str(p) for p in artwork_dir.glob("*.png")])

    if not artwork_files:
        print(f"No artwork images found in {artwork_dir}")
        # Generate a placeholder artwork
        artwork = Image.new("RGB", (aw, ah), (200, 180, 160))
        draw = ImageDraw.Draw(artwork)
        draw.rectangle([5, 5, aw - 5, ah - 5], outline=(100, 100, 100), width=3)
        draw.text((aw // 2 - 40, ah // 2 - 10), "Artwork", fill=(80, 80, 80))
        artwork_files = [None]

    # Create composite for each artwork
    mockups = []
    for i, art_path in enumerate(artwork_files):
        if art_path is None and i == 0:
            artwork = Image.new("RGB", (aw, ah), (200, 180, 160))
        elif art_path:
            artwork = Image.open(art_path).convert("RGB")
        else:
            continue

        # Resize artwork to fit placement
        artwork_resized = artwork.resize((aw, ah), Image.LANCZOS)

        # Create a frame effect (add a border)
        frame_padding = int(aw * 0.03)
        framed = Image.new("RGB", (aw + 2 * frame_padding, ah + 2 * frame_padding),
                          (40, 40, 40))
        framed.paste(artwork_resized, (frame_padding, frame_padding))

        # Rotate slightly for perspective
        if angle != 0:
            framed = framed.rotate(angle, expand=True, resample=Image.BICUBIC,
                                  fillcolor=(40, 40, 40))

        # Create a shadow layer
        shadow = Image.new("L", framed.size, 0)
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rectangle([5, 5, framed.width - 5, framed.height - 5],
                             fill=80)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))
        shadow = ImageEnhance.Brightness(shadow).enhance(0.6)

        # Composite onto room
        room_copy = room.copy()

        # Position: center frame at (cx, cy)
        paste_x = cx - framed.width // 2
        paste_y = cy - framed.height // 2

        # Apply shadow first (offset slightly down-right)
        shadow_offset_x, shadow_offset_y = 8, 12
        shadow_paste_x = paste_x + shadow_offset_x
        shadow_paste_y = paste_y + shadow_offset_y

        # Clip to image bounds
        def clip_rect(px, py, w, h, img_w, img_h):
            x1 = max(0, px)
            y1 = max(0, py)
            x2 = min(img_w, px + w)
            y2 = min(img_h, py + h)
            return x1, y1, x2 - x1, y2 - y1

        # Apply shadow
        sx1, sy1, sw, sh = clip_rect(shadow_paste_x, shadow_paste_y,
                                     framed.width, framed.height, img_w, img_h)
        if sw > 0 and sh > 0:
            shadow_region = shadow.crop((max(0, -shadow_paste_x),
                                         max(0, -shadow_paste_y),
                                         max(0, -shadow_paste_x) + sw,
                                         max(0, -shadow_paste_y) + sh))
            room_section = room_copy.crop((sx1, sy1, sx1 + sw, sy1 + sh)).convert("L")
            combined_shadow = Image.blend(room_section, shadow_region, 0.4)
            room_copy.paste(combined_shadow, (sx1, sy1))

        # Apply artwork frame
        fx1, fy1, fw, fh = clip_rect(paste_x, paste_y,
                                     framed.width, framed.height, img_w, img_h)
        if fw > 0 and fh > 0:
            frame_region = framed.crop((max(0, -paste_x),
                                       max(0, -paste_y),
                                       max(0, -paste_x) + fw,
                                       max(0, -paste_y) + fh))
            room_copy.paste(frame_region, (fx1, fy1))

        # Save output
        mockup_filename = f"mockup-artwork-{i + 1}.jpg"
        if output_path:
            base = Path(output_path)
            if base.is_dir():
                out_path = base / mockup_filename
            else:
                # Single output file: only save first mockup
                if i == 0:
                    out_path = base
                else:
                    out_path = base.parent / mockup_filename
        else:
            out_path = Path(f"/tmp/{mockup_filename}")

        room_copy.save(str(out_path), "JPEG", quality=92)
        mockups.append(str(out_path))

        # Only save the first artwork as the primary mockup for single-file output
        if i == 0:
            print(f"Primary mockup saved: {out_path}")

    print(f"Generated {len(mockups)} mockup(s)")
    return mockups


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    room_path = sys.argv[1]
    profile_path = sys.argv[2]
    art_dir = sys.argv[3]

    output_path = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = sys.argv[idx + 1]

    if not os.path.exists(room_path):
        print(f"Room photo not found: {room_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(profile_path):
        print(f"Room profile not found: {profile_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(art_dir):
        print(f"Artwork directory not found: {art_dir}", file=sys.stderr)
        sys.exit(1)

    create_mockup(room_path, profile_path, art_dir, output_path)


if __name__ == "__main__":
    main()