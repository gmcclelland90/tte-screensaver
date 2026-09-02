"""Render a punchier demo GIF: tight crop, entrance effects, readable dashboard."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from src.config import Config  # noqa: E402
from src.dashboard import build_ascii  # noqa: E402
from src.effects import EffectManager  # noqa: E402
from src.renderer import ANSIRenderer  # noqa: E402


SEQUENCE = [
    ("Slide", 200),
    ("Fireworks", 340),
    ("Unstable", 220),
]


def main() -> None:
    cfg = Config()
    cfg.use_live_dashboard = True
    cfg.clock_format = "24h"
    cfg.figlet_font = "slant"
    cfg.font_size = 24
    cfg.latitude = -41.43
    cfg.longitude = 147.14
    cfg.temperature_unit = "celsius"
    cfg.location_label = "Launceston"

    ascii_text = build_ascii(cfg)
    print("ascii preview:\n", ascii_text, flush=True)
    lines = ascii_text.splitlines()
    text_w = max((len(ln) for ln in lines), default=40)
    text_h = len(lines)

    pygame.init()
    pygame.font.init()
    renderer = ANSIRenderer(font_size=cfg.font_size, background_color=(0, 0, 0))
    canvas_w = min(90, text_w + 24)
    canvas_h = min(28, text_h + 12)
    width = canvas_w * renderer.char_width
    height = canvas_h * renderer.char_height
    print(f"canvas {canvas_w}x{canvas_h} px {width}x{height}", flush=True)

    screen = pygame.Surface((width, height))
    out_dir = Path("demo-frames")
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()

    saved = 0
    save_every = 2

    for name, budget in SEQUENCE:
        print(f"=== {name} ===", flush=True)
        manager = EffectManager(
            text=ascii_text,
            enabled_effects=[name],
            canvas_width=canvas_w,
            canvas_height=canvas_h,
            start_index=0,
            text_provider=lambda: ascii_text,  # freeze this capture's clock
            max_effect_seconds=None,
        )
        screen.fill((0, 0, 0))
        prev = {}
        for used in range(budget):
            frame = manager.get_next_frame()
            if frame is None:
                print(f"{name} finished at tte={used}", flush=True)
                break
            prev = renderer.render_frame_delta(
                frame,
                screen,
                prev,
                canvas_width=canvas_w,
                canvas_height=canvas_h,
            )
            if used % save_every == 0:
                pygame.image.save(screen, str(out_dir / f"frame_{saved:04d}.png"))
                saved += 1
            if used % 50 == 0:
                print(f"{name} tte={used}/{budget} saved={saved}", flush=True)

    pygame.quit()
    print(f"wrote {saved} frames to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
