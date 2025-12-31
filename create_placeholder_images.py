#!/usr/bin/env python3
"""
Script to create placeholder veteran images for the orbital animation.
Run this script to generate placeholder images if you don't have actual veteran photos yet.
"""

import os
from pathlib import Path

# Define the static images directory
STATIC_DIR = Path(__file__).parent / 'static' / 'images' / 'veterans'

# Ensure directory exists
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Create placeholder SVG images for veterans 6-10
placeholder_svg_template = """<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad{num}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{color1};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{color2};stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="200" height="200" fill="url(#grad{num})"/>
  <circle cx="100" cy="80" r="30" fill="rgba(255,255,255,0.9)"/>
  <rect x="70" y="120" width="60" height="80" rx="30" fill="rgba(255,255,255,0.9)"/>
  <text x="100" y="180" text-anchor="middle" fill="rgba(0,0,0,0.7)" font-family="Arial" font-size="14" font-weight="bold">Veteran {num}</text>
</svg>"""

# Color schemes for different veterans
colors = [
    ("#3498db", "#2980b9"),  # Blue
    ("#e74c3c", "#c0392b"),  # Red
    ("#2ecc71", "#27ae60"),  # Green
    ("#f39c12", "#e67e22"),  # Orange
    ("#9b59b6", "#8e44ad"),  # Purple
]

def create_placeholder_images():
    """Create placeholder SVG images for veterans 6-10"""
    for i in range(6, 11):
        color_idx = (i - 6) % len(colors)
        color1, color2 = colors[color_idx]
        
        svg_content = placeholder_svg_template.format(
            num=i,
            color1=color1,
            color2=color2
        )
        
        # Save as SVG file
        svg_path = STATIC_DIR / f'veteran{i}.svg'
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        print(f"Created placeholder: {svg_path}")

if __name__ == "__main__":
    create_placeholder_images()
    print("\n✅ Placeholder veteran images created successfully!")
    print("\nTo use your own images:")
    print("1. Copy your veteran images from D:\\_koding\\veteran\\Images\\veteram_images")
    print("2. Rename them to veteran6.jpg, veteran7.jpg, etc.")
    print("3. Place them in: static/images/veterans/")
    print("4. Update the about.html template to use .jpg instead of .svg")