"""Generate a synthetic test image simulating a living room photo for pipeline testing."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Create a 1200x800 room-like image
img = Image.new('RGB', (1200, 800), color=(210, 195, 175))
draw = ImageDraw.Draw(img)

# Wall - warm beige
draw.rectangle([(0, 0), (1200, 550)], fill=(220, 208, 188))

# Floor - hardwood
for y in range(550, 800, 8):
    shade = 160 - (y - 550) * 0.05
    draw.rectangle([(0, y), (1200, min(y+7, 800))], fill=(int(shade), int(shade*0.8), int(shade*0.5)))

# Window on left wall
draw.rectangle([(50, 60), (320, 480)], fill=(200, 220, 240))
draw.rectangle([(55, 65), (315, 475)], fill=(180, 210, 235))
# Window frame
draw.rectangle([(50, 60), (320, 480)], outline=(240, 235, 225), width=4)
draw.line([(185, 60), (185, 480)], fill=(240, 235, 225), width=3)
draw.line([(50, 270), (320, 270)], fill=(240, 235, 225), width=3)

# Light coming from window (gradient)
for i in range(1, 15):
    alpha = 5
    overlay = Image.new('RGBA', img.size, (255, 245, 225, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([(50-i*5, 60-i*3), (320+i*5, 480+i*3)], 
                          fill=(255, 245, 225, alpha))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

# Sofa - modern grey
draw.rounded_rectangle([(350, 380), (900, 540)], radius=15, fill=(80, 85, 90))
draw.rounded_rectangle([(370, 360), (880, 400)], radius=10, fill=(95, 100, 105))
# Sofa cushions
draw.rounded_rectangle([(380, 390), (530, 530)], radius=8, fill=(75, 80, 85))
draw.rounded_rectangle([(540, 390), (720, 530)], radius=8, fill=(78, 83, 88))
draw.rounded_rectangle([(730, 390), (870, 530)], radius=8, fill=(72, 77, 82))

# Sofa legs
draw.rectangle([(370, 540), (380, 555)], fill=(45, 40, 35))
draw.rectangle([(480, 540), (490, 555)], fill=(45, 40, 35))
draw.rectangle([(680, 540), (690, 555)], fill=(45, 40, 35))
draw.rectangle([(870, 540), (880, 555)], fill=(45, 40, 35))

# Coffee table - mid-century style
draw.rounded_rectangle([(500, 560), (750, 580)], radius=5, fill=(140, 110, 80))
draw.rectangle([(520, 580), (530, 600)], fill=(120, 95, 70))
draw.rectangle([(720, 580), (730, 600)], fill=(120, 95, 70))

# Art on wall (empty frame for now - will contrast)
draw.rectangle([(550, 140), (780, 380)], fill=(180, 170, 155), outline=(195, 185, 170), width=3)

# Floor lamp (right side)
draw.rectangle([(960, 250), (965, 550)], fill=(60, 55, 50))
draw.ellipse([(940, 230), (985, 265)], fill=(230, 200, 170))
draw.ellipse([(945, 235), (980, 260)], fill=(245, 220, 190))

# Light glow from lamp
overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
overlay_draw = ImageDraw.Draw(overlay)
for r in range(50, 200, 10):
    overlay_draw.ellipse([(960-r, 260-r), (960+r, 260+r)], 
                        fill=(255, 230, 200, max(0, 8 - r//30)))
img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
draw = ImageDraw.Draw(img)

# Rug under coffee table
draw.rounded_rectangle([(420, 545), (830, 650)], radius=20, fill=(150, 160, 170, 180), 
                      outline=(130, 140, 150), width=2)

# Pillows on sofa
draw.ellipse([(380, 370), (430, 410)], fill=(180, 120, 100))
draw.ellipse([(440, 368), (490, 408)], fill=(60, 80, 120))
draw.ellipse([(840, 372), (890, 410)], fill=(180, 160, 100))

# Crown molding
draw.rectangle([(0, 0), (1200, 12)], fill=(235, 225, 210))
draw.rectangle([(0, 12), (1200, 16)], fill=(230, 220, 205))

# Baseboard
draw.rectangle([(0, 550), (1200, 558)], fill=(215, 205, 190))
draw.rectangle([(0, 558), (1200, 565)], fill=(210, 200, 185))

# Add some noise/texture
np_img = np.array(img)
noise = np.random.normal(0, 3, np_img.shape).astype(np.int16)
np_img = np.clip(np_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
img = Image.fromarray(np_img)

# Add slight blur for realism
img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

output_path = '/home/team/shared/ai-pipeline/test_room.jpg'
img.save(output_path, quality=92)
print(f"Test image saved to: {output_path}")
print(f"Size: {img.size}")
