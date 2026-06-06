import os
from PIL import Image

input_path = '/Users/lizasutova/.gemini/antigravity/brain/e67f989e-54ea-4120-8a2a-7c0d3149e316/media__1780678165450.png'
output_path = '/Users/lizasutova/.gemini/antigravity/scratch/cfo-investment-portal/invest_matrix_theme.png'

print(f"Loading image from {input_path}")
img = Image.open(input_path)
img = img.convert('RGBA')
width, height = img.size
data = img.load()

visited = set()
queue = []

def is_background(x, y):
    r, g, b, a = data[x, y]
    # Check if pixel is white/light gray
    return r > 240 and g > 240 and b > 240

# Add all border pixels that match background
for x in range(width):
    if is_background(x, 0):
        queue.append((x, 0))
        visited.add((x, 0))
    if is_background(x, height - 1):
        queue.append((x, height - 1))
        visited.add((x, height - 1))

for y in range(height):
    if is_background(0, y):
        queue.append((0, y))
        visited.add((0, y))
    if is_background(width - 1, y):
        queue.append((width - 1, y))
        visited.add((width - 1, y))

# BFS flood fill
idx = 0
while idx < len(queue):
    cx, cy = queue[idx]
    idx += 1
    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
        nx, ny = cx + dx, cy + dy
        if 0 <= nx < width and 0 <= ny < height:
            if (nx, ny) not in visited and is_background(nx, ny):
                visited.add((nx, ny))
                queue.append((nx, ny))

# Set visited pixels to transparent
for x, y in visited:
    data[x, y] = (0, 0, 0, 0)

# Smooth transition edges
for y in range(height):
    for x in range(width):
        if (x, y) not in visited:
            has_bg_neighbor = False
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) in visited:
                    has_bg_neighbor = True
                    break
            if has_bg_neighbor:
                r, g, b, a = data[x, y]
                avg = (r + g + b) / 3.0
                if avg > 200:
                    alpha = int((255.0 - avg) / 55.0 * 255.0)
                    data[x, y] = (r, g, b, alpha)

# Save processed transparent image
img.save(output_path, 'PNG')
print(f"Saved transparent image to {output_path}")
