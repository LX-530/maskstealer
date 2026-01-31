"""
Generate a pixel-style dungeon background image.
"""

from __future__ import annotations

from PIL import Image, ImageDraw
import os
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def resource_path(*relative_parts: str) -> str:
    return str(ROOT.joinpath(*relative_parts))


def _clamp_channel(value: int) -> int:
    return max(0, min(255, value))


def _shade(color, delta):
    return (
        _clamp_channel(color[0] + delta),
        _clamp_channel(color[1] + delta),
        _clamp_channel(color[2] + delta),
    )


def create_dungeon_background(
    width: int = 1024,
    height: int = 768,
    output_path: str | None = None,
    scale: int = 4,
    seed: int = 42,
) -> str:
    """Create a pixel-style dungeon background and save it to disk."""
    if output_path is None:
        output_path = resource_path("images", "background", "Background.png")

    base_w = max(1, width // scale)
    base_h = max(1, height // scale)
    rng = random.Random(seed)

    base_color = (44, 42, 48)
    img = Image.new("RGBA", (base_w, base_h), base_color)
    draw = ImageDraw.Draw(img)

    tile = 8
    palette = [
        (52, 50, 56),
        (58, 56, 62),
        (46, 44, 50),
        (40, 38, 44),
    ]

    for ty in range(0, base_h, tile):
        for tx in range(0, base_w, tile):
            color = rng.choice(palette)
            draw.rectangle([tx, ty, tx + tile - 1, ty + tile - 1], fill=color)

            if rng.random() < 0.35:
                crack_color = _shade(color, -12)
                x0 = tx + rng.randint(1, tile - 3)
                y0 = ty + rng.randint(1, tile - 3)
                draw.line([x0, y0, x0 + rng.randint(1, 3), y0 + rng.randint(1, 3)], fill=crack_color)

            if rng.random() < 0.2:
                moss_color = (46, 65, 52)
                for _ in range(3):
                    mx = tx + rng.randint(1, tile - 2)
                    my = ty + rng.randint(1, tile - 2)
                    draw.point((mx, my), fill=moss_color)

    # Add rugs
    for _ in range(3):
        rug_w = rng.randint(32, 48)
        rug_h = rng.randint(18, 24)
        rx = rng.randint(6, base_w - rug_w - 6)
        ry = rng.randint(6, base_h - rug_h - 6)
        rug_color = (110, 40, 42)
        border_color = (140, 70, 60)
        draw.rectangle([rx, ry, rx + rug_w, ry + rug_h], fill=rug_color)
        draw.rectangle([rx, ry, rx + rug_w, ry + rug_h], outline=border_color)

    # Columns and crates
    for _ in range(10):
        cx = rng.randint(6, base_w - 10)
        cy = rng.randint(6, base_h - 14)
        pillar_color = (70, 68, 76)
        shadow_color = (32, 30, 36)
        draw.rectangle([cx, cy, cx + 6, cy + 12], fill=pillar_color)
        draw.rectangle([cx, cy, cx + 6, cy + 12], outline=shadow_color)
        draw.rectangle([cx + 1, cy + 1, cx + 2, cy + 11], fill=_shade(pillar_color, 12))

    for _ in range(8):
        bx = rng.randint(6, base_w - 12)
        by = rng.randint(6, base_h - 12)
        box_color = (86, 58, 34)
        box_border = (40, 28, 18)
        draw.rectangle([bx, by, bx + 6, by + 6], fill=box_color)
        draw.rectangle([bx, by, bx + 6, by + 6], outline=box_border)
        draw.line([bx, by + 3, bx + 6, by + 3], fill=_shade(box_color, 16))

    # Torch glows
    glow = Image.new("RGBA", (base_w, base_h), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for _ in range(6):
        tx = rng.randint(8, base_w - 8)
        ty = rng.randint(8, base_h - 8)
        torch_color = (220, 150, 70)
        draw.rectangle([tx - 1, ty - 2, tx + 1, ty + 2], fill=torch_color)
        glow_draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(255, 180, 90, 80))
        glow_draw.ellipse([tx - 10, ty - 10, tx + 10, ty + 10], fill=(255, 120, 60, 40))

    img = Image.alpha_composite(img, glow)

    # Vignette
    vignette = Image.new("RGBA", (base_w, base_h), (0, 0, 0, 0))
    vignette_draw = ImageDraw.Draw(vignette)
    limit = min(base_w, base_h) // 2
    for i in range(limit):
        alpha = int(120 * (i / limit) ** 2)
        vignette_draw.rectangle(
            [i, i, base_w - i - 1, base_h - i - 1],
            outline=(0, 0, 0, alpha),
        )
    img = Image.alpha_composite(img, vignette)

    # Scale up with nearest neighbor to keep pixel style
    img = img.resize((width, height), Image.NEAREST).convert("RGB")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Background generated: {output_path}")
    return output_path


if __name__ == "__main__":
    create_dungeon_background()
