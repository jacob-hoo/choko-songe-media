"""대본 → 세로 영상(mp4) + 인스타 캐러셀(png)."""
import subprocess
import tempfile
import textwrap
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import (ACCENT, BG, BRANDS, DISCLOSURE_SHORT, FONT_BOLD, FONT_REG,
                    H, INK, SCENE_SEC, W)


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _product_image(url: str) -> Image.Image | None:
    if not url:
        return None
    try:
        if url.startswith("http"):
            with urllib.request.urlopen(url, timeout=15) as r, tempfile.NamedTemporaryFile() as f:
                f.write(r.read())
                f.flush()
                return Image.open(f.name).convert("RGB")
        return Image.open(url).convert("RGB")
    except Exception:
        return None


def _centered(draw: ImageDraw.ImageDraw, text: str, y: int, font, fill, width_chars: int) -> int:
    for line in textwrap.wrap(text, width_chars) or [""]:
        w = draw.textlength(line, font=font)
        draw.text(((W - w) / 2, y), line, font=font, fill=fill)
        y += int(font.size * 1.3)
    return y


def _frame(headline: str, sub: str, idx: int, total: int, img: Image.Image | None,
           price: str = "", size=(W, H), footer: str = "") -> Image.Image:
    w, h = size
    im = Image.new("RGB", size, BG)
    d = ImageDraw.Draw(im)
    # 대가성 표시: 모든 장면 상단에 고정 (일부만 보는 시청자 대응)
    d.rectangle([0, 0, w, 96], fill=INK)
    tag = _font(FONT_REG, 34)
    d.text(((w - d.textlength(DISCLOSURE_SHORT, font=tag)) / 2, 28), DISCLOSURE_SHORT, font=tag, fill=(255, 255, 255))
    # 진행 바
    d.rectangle([60, 130, 60 + (w - 120) * (idx + 1) / total, 140], fill=ACCENT)
    # 상품 이미지 영역
    box_top, box_h = 200, int(h * 0.42)
    if img:
        im_c = img.copy()
        im_c.thumbnail((w - 160, box_h))
        im.paste(im_c, ((w - im_c.width) // 2, box_top + (box_h - im_c.height) // 2))
    else:
        d.rounded_rectangle([80, box_top, w - 80, box_top + box_h], 40, fill=(236, 230, 218))
    y = box_top + box_h + 80
    y = _centered(d, headline, y, _font(FONT_BOLD, 84 if w == W else 72), INK, 12)
    if sub:
        _centered(d, sub, y + 30, _font(FONT_REG, 48), (90, 90, 96), 20)
    if price:
        f = _font(FONT_BOLD, 64)
        d.text(((w - d.textlength(price, font=f)) / 2, h - 360), price, font=f, fill=ACCENT)
    foot = _font(FONT_REG, 36)
    d.text(((w - d.textlength(footer, font=foot)) / 2, h - 140), footer, font=foot, fill=(120, 120, 126))
    return im


def render_video(row: dict, script: dict, out_mp4: Path) -> None:
    img = _product_image(row.get("image", ""))
    price = f"{int(row['price']):,}원" if row["price"].isdigit() else ""
    scenes = [(script["hook"], row["name"], "")]
    scenes += [(p, "", "") for p in script["points"]]
    scenes += [(script["verdict"], "", price), (f"댓글에 「{row.get('dm_keyword') or '링크'}」", f"DM 링크 · 프로필 {int(''.join(c for c in row['product_id'] if c.isdigit()) or 0)}번", "")]
    with tempfile.TemporaryDirectory() as tmp:
        for i, (head, sub, pr) in enumerate(scenes):
            _frame(head, sub, i, len(scenes), img, pr, footer=BRANDS[row['brand']]['name']).save(f"{tmp}/{i:02d}.png")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", f"1/{SCENE_SEC}",
               "-i", f"{tmp}/%02d.png", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
               "-shortest", "-vf", "fps=30,format=yuv420p", "-c:v", "libx264",
               "-c:a", "aac", "-movflags", "+faststart", str(out_mp4)]
        subprocess.run(cmd, check=True)


def render_carousel(row: dict, script: dict, out_dir: Path) -> list[Path]:
    img = _product_image(row.get("image", ""))
    pages = script["carousel"][:7] + ["저장해두고 필요할 때 보세요"]
    paths = []
    for i, text in enumerate(pages):
        p = out_dir / f"card_{i + 1}.jpg"  # 틱톡 사진은 PNG 불가
        _frame(text, "", i, len(pages), img if i == 0 else None, size=(1080, 1350),
               footer=BRANDS[row["brand"]]["name"]).save(p, quality=92)
        paths.append(p)
    return paths
