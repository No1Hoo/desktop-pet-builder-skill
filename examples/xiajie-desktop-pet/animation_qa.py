from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    root = Path(__file__).resolve().parent
    frames_dir = root / "assets" / "frames"
    actions = ("idle", "walk", "wave", "pat", "feed", "sleep")
    cell = (230, 430)
    sheet = Image.new("RGBA", (cell[0] * 4, cell[1] * len(actions)), (239, 239, 239, 255))
    draw = ImageDraw.Draw(sheet)
    for row, action in enumerate(actions):
        for column, path in enumerate(sorted(frames_dir.glob(f"{action}_*.png"))):
            frame = Image.open(path).convert("RGBA")
            frame.thumbnail((cell[0] - 20, cell[1] - 42))
            x = column * cell[0] + (cell[0] - frame.width) // 2
            y = row * cell[1] + cell[1] - frame.height - 12
            sheet.alpha_composite(frame, (x, y))
            draw.text((column * cell[0] + 8, row * cell[1] + 8), f"{action} {column + 1}", fill=(40, 40, 40, 255))
    output = root / "qa" / "animation-frames.png"
    output.parent.mkdir(exist_ok=True)
    sheet.save(output)
    print(output)


if __name__ == "__main__":
    main()
