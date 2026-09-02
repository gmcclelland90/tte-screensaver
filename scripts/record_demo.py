"""Render a short demo GIF using the real pygame/TTE pipeline (offscreen)."""
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


def main() -> None:
    width, height = 1280, 720
    # Consume plenty of TTE frames so ColorShift actually cycles.
    tte_frames = 240
    save_every = 2  # 120 PNGs -> ~10s at 12fps

    cfg = Config()
    cfg.use_live_dashboard = True
    cfg.clock_format = "24h"
    cfg.figlet_font = "slant"
    cfg.font_size = 22
    cfg.latitude = -41.43
    cfg.longitude = 147.14
    cfg.temperature_unit = "celsius"
    cfg.location_label = "Launceston"
    cfg.enabled_effects = ["ColorShift", "Waves", "Sweep"]

    pygame.init()
    pygame.font.init()
    screen = pygame.Surface((width, height))
    renderer = ANSIRenderer(font_size=cfg.font_size, background_color=(0, 0, 0))
    canvas_w = width // renderer.char_width
    canvas_h = height // renderer.char_height

    ascii_text = build_ascii(cfg)
    print("ascii preview:\n", ascii_text[:400], flush=True)

    manager = EffectManager(
        text=ascii_text,
        enabled_effects=cfg.enabled_effects,
        canvas_width=canvas_w,
        canvas_height=canvas_h,
        start_index=0,
        text_provider=lambda: build_ascii(cfg),
        max_effect_seconds=None,  # let ColorShift run; switch on StopIteration
    )

    out_dir = Path("demo-frames")
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()

    screen.fill((0, 0, 0))
    prev = {}
    saved = 0
    switches = 0
    for i in range(tte_frames):
        frame = manager.get_next_frame()
        if frame is None:
            if switches >= 2:
                break
            manager.switch_to_next_effect()
            prev = {}
            screen.fill((0, 0, 0))
            frame = manager.get_next_frame()
            switches += 1
            print(f"switched to {manager.get_current_effect_name()}", flush=True)
        if frame:
            prev = renderer.render_frame_delta(
                frame,
                screen,
                prev,
                canvas_width=canvas_w,
                canvas_height=canvas_h,
            )
        if i % save_every == 0:
            path = out_dir / f"frame_{saved:04d}.png"
            pygame.image.save(screen, str(path))
            saved += 1
        if i % 30 == 0:
            print(
                f"tte={i}/{tte_frames} saved={saved} effect={manager.get_current_effect_name()}",
                flush=True,
            )

    pygame.quit()
    print(f"wrote {saved} frames to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
