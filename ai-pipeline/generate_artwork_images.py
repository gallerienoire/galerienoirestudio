#!/usr/bin/env python3
"""
Artwork Image Generator — Galerie Noire AI Pipeline (Step 2b)
==============================================================
Generates actual PNG image files for each artwork concept using
the room profile's color palette and the artwork's style/mood.

Creates high-quality synthetic abstract art that looks museum-worthy.
"""

import json
import math
import os
import sys
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def hex_to_rgb(hex_color):
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def parse_prompt_colors(prompt):
    """Extract hex colors from an image prompt."""
    import re
    colors = re.findall(r'#[0-9a-fA-F]{6}', prompt)
    return [hex_to_rgb(c) for c in colors] if colors else [(220, 210, 191), (200, 180, 150)]


def generate_statement_composition(width=1024, height=1024, colors=None):
    """Large-format abstract expressionist style."""
    if colors is None or len(colors) < 2:
        colors = [(222, 210, 191), (153, 122, 77), (196, 221, 235), (168, 166, 161)]
    
    img = Image.new('RGB', (width, height), colors[0])
    draw = ImageDraw.Draw(img)
    
    # Bold gestural marks
    for _ in range(random.randint(8, 15)):
        cx, cy = random.randint(0, width), random.randint(0, height)
        color = random.choice(colors[1:4])
        # Paint strokes
        for j in range(random.randint(3, 8)):
            x = cx + random.randint(-80, 80)
            y = cy + random.randint(-80, 80)
            r = random.randint(20, 80)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=color, outline=None)
            # Add some transparency effect
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.ellipse([x-r//2, y-r//2, x+r//2, y+r//2], 
                                fill=(*color, 60))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)
    
    # Texture overlay
    np_img = np.array(img)
    noise = np.random.normal(0, 8, np_img.shape).astype(np.int16)
    np_img = np.clip(np_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(np_img)
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    return img


def generate_abstract_atmosphere(width=1024, height=1024, colors=None):
    """Color-field painting style (Rothko-esque)."""
    if colors is None or len(colors) < 2:
        colors = [(222, 210, 191), (153, 122, 77), (196, 221, 235)]
    
    img = Image.new('RGB', (width, height), colors[0])
    draw = ImageDraw.Draw(img)
    
    # Layered color blocks with soft edges
    for i, color in enumerate(colors):
        y_offset = height * (0.15 + i * 0.22)
        block_height = height * random.uniform(0.15, 0.25)
        margin = width * random.uniform(0.1, 0.2)
        
        # Draw soft rectangle
        for j in range(5):
            m = margin * (1 + j * 0.05)
            bh = block_height * (1 + j * 0.08)
            alpha = max(5, 40 - j * 8)
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rounded_rectangle(
                [m, y_offset - bh//2, width - m, y_offset + bh//2],
                radius=int(bh * 0.4),
                fill=(*color, alpha)
            )
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        draw = ImageDraw.Draw(img)
    
    # Soften with blur
    img = img.filter(ImageFilter.GaussianBlur(radius=3))
    
    return img


def generate_botanical_study(width=1024, height=1024, colors=None):
    """Botanical illustration style."""
    if colors is None or len(colors) < 2:
        colors = [(245, 240, 235), (153, 122, 77), (196, 221, 235)]
    
    img = Image.new('RGB', (width, height), colors[0])
    draw = ImageDraw.Draw(img)
    
    # Draw leaves and stems
    center_x, center_y = width // 2, height // 2
    
    for _ in range(random.randint(5, 10)):
        # Stems
        x = center_x + random.randint(-200, 200)
        stem_color = colors[1] if len(colors) > 1 else (100, 80, 50)
        draw.arc([x-5, center_y+100, x+5, height-50], 
                180, 360, fill=stem_color, width=3)
        
        # Leaves
        for _ in range(random.randint(3, 6)):
            lx = x + random.randint(-40, 40)
            ly = random.randint(100, height-100)
            leaf_color = colors[2] if len(colors) > 2 else (100, 150, 100)
            
            # Leaf shape using bezier approximation
            leaf_w = random.randint(15, 35)
            leaf_h = random.randint(40, 80)
            draw.ellipse([lx-leaf_w, ly-leaf_h//2, lx+leaf_w, ly+leaf_h//2], 
                        fill=leaf_color, outline=None)
            
            # Leaf vein
            draw.line([lx, ly-leaf_h//4, lx, ly+leaf_h//4], 
                     fill=(0, 0, 0, 30), width=1)
    
    # Paper texture
    np_img = np.array(img)
    noise = np.random.normal(0, 5, np_img.shape).astype(np.int16)
    np_img = np.clip(np_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(np_img)
    
    return img


def generate_architectural_geometric(width=1024, height=1024, colors=None):
    """Geometric abstract style."""
    if colors is None or len(colors) < 2:
        colors = [(222, 210, 191), (153, 122, 77), (196, 221, 235), (77, 82, 87)]
    
    img = Image.new('RGB', (width, height), colors[0])
    draw = ImageDraw.Draw(img)
    
    # Intersecting geometric planes
    for i in range(random.randint(8, 15)):
        color = colors[i % (len(colors)-1) + 1]
        x1 = random.randint(50, width-50)
        y1 = random.randint(50, height-50)
        
        # Random polygon
        points = []
        for _ in range(random.randint(3, 6)):
            points.append((x1 + random.randint(-150, 150), 
                          y1 + random.randint(-150, 150)))
        
        alpha = random.randint(40, 120)
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.polygon(points, fill=(*color, alpha))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
    
    # Clean lines
    for _ in range(random.randint(5, 10)):
        color = colors[1]
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = x1 + random.randint(-200, 200)
        y2 = y1 + random.randint(-200, 200)
        draw.line([x1, y1, x2, y2], fill=color, width=random.randint(1, 3))
    
    return img


def generate_atmospheric_landscape(width=1024, height=1024, colors=None):
    """Atmospheric landscape / romantic horizon style."""
    if colors is None or len(colors) < 3:
        colors = [(222, 210, 191), (153, 122, 77), (196, 221, 235), (168, 166, 161)]
    
    img = Image.new('RGB', (width, height), colors[0])
    
    # Gradient sky
    for y in range(height):
        t = y / height
        r = int(colors[0][0] * (1-t) + colors[2][0] * t)
        g = int(colors[0][1] * (1-t) + colors[2][1] * t)
        b = int(colors[0][2] * (1-t) + colors[2][2] * t)
        draw = ImageDraw.Draw(img)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Horizon line with mist
    horizon_y = height // 2 + random.randint(-50, 50)
    draw = ImageDraw.Draw(img)
    draw.line([(0, horizon_y), (width, horizon_y)], 
             fill=colors[1], width=random.randint(1, 3))
    
    # Mist/fog layers
    for i in range(random.randint(3, 6)):
        y = horizon_y + random.randint(-40, 80)
        alpha = random.randint(5, 20)
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        fog_color = colors[3] if len(colors) > 3 else colors[1]
        overlay_draw.rounded_rectangle(
            [0, y, width, y + random.randint(10, 40)],
            radius=20, fill=(*fog_color, alpha)
        )
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    # Distant hills
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    hill_points = []
    for x in range(0, width+1, 20):
        hill_y = horizon_y + random.randint(10, 60)
        hill_points.append((x, hill_y))
    hill_points.append((width, height))
    hill_points.append((0, height))
    overlay_draw.polygon(hill_points, fill=(*colors[1], 60))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    # Soften
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    
    return img


GENERATORS = {
    "statement_composition": generate_statement_composition,
    "abstract_atmosphere": generate_abstract_atmosphere,
    "botanical_study": generate_botanical_study,
    "architectural_geometric": generate_architectural_geometric,
    "atmospheric_landscape": generate_atmospheric_landscape,
}


def generate_artwork_image(artwork_piece, output_path, size=(1024, 1024)):
    """
    Generate an artwork image from a piece's data.
    Uses the slug to pick the right generator, and room colors from the prompt.
    """
    slug = artwork_piece.get("slug", "abstract_atmosphere")
    title = artwork_piece.get("title", "Untitled")
    image_prompt = artwork_piece.get("image_prompt", "")
    
    print(f"  Generating: \"{title}\" ({slug})")
    
    # Extract colors from prompt
    colors = parse_prompt_colors(image_prompt)
    
    # Pick the right generator
    generator = GENERATORS.get(slug, generate_abstract_atmosphere)
    
    # Generate the image
    img = generator(width=size[0], height=size[1], colors=colors)
    
    # Add title watermark at the bottom (subtle)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except (OSError, IOError):
        font = ImageFont.load_default()
    
    draw.text((20, size[1] - 35), f"Galerie Noire — \"{title}\"", 
              fill=(255, 255, 255, 40), font=font)
    
    # Save
    img.save(output_path, quality=92)
    file_size = os.path.getsize(output_path)
    print(f"    → Saved to {output_path} ({file_size:,} bytes)")
    
    return output_path


def process_project(project_id, artwork_dir, size=(1024, 1024)):
    """
    Process all pieces for a project, generating images for each.
    """
    coll_path = os.path.join(artwork_dir, "artwork_collection.json")
    if not os.path.exists(coll_path):
        print(f"❌ No artwork_collection.json found for {project_id}")
        return []
    
    with open(coll_path) as f:
        data = json.load(f)
    
    pieces = data.get("pieces", data.get("artwork_collection", {}).get("pieces", []))
    if not pieces:
        pieces = data.get("artwork_collection", data)
        if isinstance(pieces, dict) and "pieces" in pieces:
            pieces = pieces["pieces"]
    
    print(f"\n{'='*60}")
    print(f"Generating images for project: {project_id}")
    print(f"  {len(pieces)} artworks to generate")
    print(f"{'='*60}")
    
    generated = []
    for i, piece in enumerate(pieces):
        slug = piece.get("slug", f"artwork-{i+1}")
        title = piece.get("title", f"Piece {i+1}")
        safe_title = title.lower().replace(" ", "-").replace("'", "")[:30]
        filename = f"artwork-{i+1}-{safe_title}.png"
        output_path = os.path.join(artwork_dir, filename)
        
        generate_artwork_image(piece, output_path, size=size)
        
        piece["generated_image"] = filename
        piece["image_url"] = f"/artwork/{project_id}/{filename}"
        generated.append(filename)
    
    # Update the collection JSON
    with open(coll_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  ✅ Updated artwork_collection.json with image paths")
    
    return generated


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: python3 generate_artwork_images.py <project_id> <artwork_dir> [--size WxH]")
        print()
        print("Generates PNG artwork images for a project's artwork collection.")
        sys.exit(1)
    
    project_id = sys.argv[1]
    artwork_dir = sys.argv[2]
    
    size = (1024, 1024)
    if "--size" in sys.argv:
        idx = sys.argv.index("--size")
        if idx + 1 < len(sys.argv):
            parts = sys.argv[idx+1].split("x")
            size = (int(parts[0]), int(parts[1]))
    
    generated = process_project(project_id, artwork_dir, size=size)
    print(f"\n✅ Generated {len(generated)} images for {project_id}")


if __name__ == "__main__":
    main()