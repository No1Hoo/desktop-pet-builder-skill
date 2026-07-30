from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw
from PySide6.QtWidgets import QApplication

from main import DesktopPet


def main() -> None:
    app = QApplication([])
    pet = DesktopPet()
    pet.move(0, 0)
    pet.show()
    out_dir = Path(__file__).resolve().parent / "qa"
    out_dir.mkdir(exist_ok=True)
    states = ("idle", "chat", "pat", "feed", "walk", "sleep", "jump", "shake")
    frames: list[tuple[str, Image.Image]] = []
    for state in states:
        pet.activate(state)
        pet.show_bubble(f"视觉检查：{state}", 60)
        pet.bubble_started -= 5
        for _ in range(36):
            pet.tick()
            app.processEvents()
        path = out_dir / f"{state}.png"
        pet.grab().save(str(path))
        frames.append((state, Image.open(path).convert("RGBA")))

    thumb_size = (280, 510)
    sheet = Image.new("RGBA", (thumb_size[0] * 4, thumb_size[1] * 2), (238, 238, 238, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (name, frame) in enumerate(frames):
        frame.thumbnail((thumb_size[0] - 10, thumb_size[1] - 30))
        x = (index % 4) * thumb_size[0] + (thumb_size[0] - frame.width) // 2
        y = (index // 4) * thumb_size[1] + 24
        sheet.alpha_composite(frame, (x, y))
        draw.text(((index % 4) * thumb_size[0] + 8, (index // 4) * thumb_size[1] + 5), name, fill=(50, 45, 52, 255))
    sheet.save(out_dir / "contact-sheet.png")
    print(out_dir / "contact-sheet.png")


if __name__ == "__main__":
    main()
