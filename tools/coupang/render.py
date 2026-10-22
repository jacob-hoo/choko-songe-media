"""대본 → 세로 영상(mp4) + 인스타 캐러셀(png)."""
import subprocess
import sys
import tempfile
import textwrap
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bgm  # noqa: E402  공용 배경음악

from config import (ACCENT, BG, BRANDS, DISCLOSURE_SHORT, DM_ENABLED, FONT_BOLD, FONT_REG,
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


def _card(headline: str, sub: str, idx: int, total: int, img: Image.Image | None,
          price: str, footer: str) -> Image.Image:
    """캐러셀 전용 1080x1350 배치. 그림 없는 장은 글을 가운데 크게 둔다."""
    w, h = 1080, 1350
    im = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 90], fill=INK)
    tag = _font(FONT_REG, 32)
    d.text(((w - d.textlength(DISCLOSURE_SHORT, font=tag)) / 2, 26), DISCLOSURE_SHORT, font=tag, fill=(255, 255, 255))
    d.rectangle([60, 120, 60 + (w - 120) * (idx + 1) / total, 128], fill=ACCENT)
    hf, sf = _font(FONT_BOLD, 76), _font(FONT_REG, 44)

    def block(text, y, fnt, fill, width):
        for line in textwrap.wrap(text, width) or [""]:
            d.text(((w - d.textlength(line, font=fnt)) / 2, y), line, font=fnt, fill=fill)
            y += int(fnt.size * 1.3)
        return y

    if img:
        c = img.copy()
        c.thumbnail((w - 240, 560))
        im.paste(c, ((w - c.width) // 2, 170 + (560 - c.height) // 2))
        y = 780
    else:
        lines = len(textwrap.wrap(headline, 11)) + (len(textwrap.wrap(sub, 20)) if sub else 0)
        y = max(260, (h - lines * 100) // 2 - 80)
    y = block(headline, y, hf, INK, 11)
    if sub:
        y = block(sub, y + 24, sf, (90, 90, 96), 20)
    if price:
        pf = _font(FONT_BOLD, 60)
        d.text(((w - d.textlength(price, font=pf)) / 2, y + 40), price, font=pf, fill=ACCENT)
    ff = _font(FONT_REG, 34)
    d.text(((w - d.textlength(footer, font=ff)) / 2, h - 80), footer, font=ff, fill=(120, 120, 126))
    return im


def _motion() -> str:
    """장면마다 천천히 다가가는 화면(위쪽 고정: 대가성 띠가 잘리지 않게). 멈춘 화면은 첫 1초에 넘겨진다(2026-10-21 기준선: 평균 시청 1.3~4초)."""
    frames = int(SCENE_SEC * 30)
    return (f"scale={W * 2}:{H * 2},zoompan=z='min(zoom+0.0008,1.04)':d={frames}"
            f":x='iw/2-(iw/zoom/2)':y=0:s={W}x{H}:fps=30,format=yuv420p")


def _chime(seconds: float) -> str:
    """장면이 바뀔 때마다 짧은 맑은 소리(직접 합성, 저작권 없음). 무음 영상은 소리 켠 시청자가 바로 넘긴다."""
    k = SCENE_SEC
    expr = (f"0.10*sin(2*PI*880*t)*exp(-7*mod(t\\,{k}))"
            f"+0.05*sin(2*PI*1318.5*t)*exp(-9*mod(t\\,{k}))")
    return f"aevalsrc=exprs={expr}|{expr}:s=44100:d={seconds}"


def render_video(row: dict, script: dict, out_mp4: Path) -> None:
    img = _product_image(row.get("image", ""))
    price = f"{int(row['price']):,}원" if row["price"].isdigit() else ""
    scenes = [(script["hook"], row["name"], "")]
    scenes += [(p, "", "") for p in script["points"]]
    scenes += [(script["verdict"], "", price), ((f"댓글에 「{row.get('dm_keyword') or '링크'}」", f"DM 링크 · 프로필 {int(''.join(c for c in row['product_id'] if c.isdigit()) or 0)}번", "")
               if DM_ENABLED else (f"프로필 링크 {int(''.join(c for c in row['product_id'] if c.isdigit()) or 0)}번", "제품 모음에서 보세요", ""))]
    # 공용 배경음악(Suno). 없으면 장면 전환 효과음.
    track = bgm.pick(row["brand"], row["product_id"])
    if track:
        audio_in, af = bgm.ffmpeg_audio_args(track, len(scenes) * SCENE_SEC)
    else:
        audio_in, af = ["-f", "lavfi", "-i", _chime(len(scenes) * SCENE_SEC)], "anull"
    with tempfile.TemporaryDirectory() as tmp:
        for i, (head, sub, pr) in enumerate(scenes):
            _frame(head, sub, i, len(scenes), img, pr, footer=BRANDS[row['brand']]['name']).save(f"{tmp}/{i:02d}.png")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", f"1/{SCENE_SEC}",
               "-i", f"{tmp}/%02d.png", *audio_in,
               "-shortest", "-vf", _motion(), "-af", af, "-c:v", "libx264",
               "-c:a", "aac", "-movflags", "+faststart", str(out_mp4)]
        subprocess.run(cmd, check=True)


def render_carousel(row: dict, script: dict, out_dir: Path) -> list[Path]:
    """쿠팡 상품 캐러셀 5장 (1080x1350).

    1장 훅+상품(상단 광고 표시) / 2~3장 편익 / 4장 맞는 사람·주의점 / 5장 댓글 키워드.
    2026-10-21 AI 인스타 운영 영상 7편 분석: 상품 캐러셀은 4~5장, 같은 내용 릴스와 묶어 올린다.
    """
    img = _product_image(row.get("image", ""))
    kw = row.get("dm_keyword") or "링크"
    no = int("".join(c for c in row["product_id"] if c.isdigit()) or 0)
    price = f"{int(row['price']):,}원" if row["price"].isdigit() else ""
    pts = (script["points"] + ["", ""])[:2]
    pages = [
        (script["hook"], row["name"], img, ""),
        (pts[0], "", None, ""),
        (pts[1], "", None, ""),
        (script["verdict"], "이런 분께 맞아요", None, price),
        ((f"댓글에 「{kw}」", f"DM으로 링크를 보내 드려요 · 프로필 {no}번", None, "") if DM_ENABLED
         else (f"프로필 링크 {no}번", "저장해 두면 필요할 때 다시 볼 수 있어요", None, "")),
    ]
    paths = []
    for i, (head, sub, im, pr) in enumerate(pages):
        p = out_dir / f"card_{i + 1}.jpg"  # 틱톡 사진은 PNG 불가
        _card(head, sub, i, len(pages), im, pr, BRANDS[row["brand"]]["name"]).save(p, quality=92)
        paths.append(p)
    return paths
