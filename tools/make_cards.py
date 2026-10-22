"""초코송이 지혜카드 제작기: topics.json -> out/<id>.png (1080x1920) + out/<id>.mp4 (7초).

캐릭터: characters/<speaker>/pose.png 가 있으면 그 그림을 쓰고, 없으면 임시 도형 캐릭터를 그린다.
사용: .venv\\Scripts\\python.exe make_cards.py [--only 001-...] [--no-video]
"""
import argparse
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
OUT = ROOT / "out"
W, H = 1080, 1920
# 한글 폰트: 리눅스(클로드 PC)는 Noto Sans CJK(OFL, 상업 사용 무료, apt fonts-noto-cjk), 윈도우는 맑은고딕
_FONT_CANDIDATES = [
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/malgunbd.ttf"),
]
FONT, FONT_BOLD = next(((r, b) for r, b in _FONT_CANDIDATES if Path(r).exists()), _FONT_CANDIDATES[-1])
HANDLE = "@choko_songe_family"
VIDEO_SECONDS = 7

# 색: 따뜻한 크림 배경 + 초코 브라운
BG = (255, 247, 234)
INK = (58, 40, 30)
SUB = (130, 105, 90)
ACCENT = {"choko": (122, 74, 44), "song-e": (226, 160, 92)}

# 브랜드별 테마. topics.json 항목에 "brand"가 없으면 초코송이.
# 화자(speaker)가 초코·송이면 강아지, 그 밖에는 브랜드 상징 원(글자 한 자)을 그린다.
BRANDS = {
    "choko": {"bg": BG, "ink": INK, "sub": SUB, "badge": "초코송이 하루 한 장", "handle": HANDLE, "scale": 1.0,
              "speakers": {"choko": ACCENT["choko"], "song-e": ACCENT["song-e"]}},
    "silver": {"bg": (246, 250, 244), "ink": (24, 44, 32), "sub": (80, 100, 88), "badge": "봄날 수첩 · 부모님 생활 정보", "handle": "@ljw57183800", "scale": 1.15,
               "speakers": {"silver": (46, 110, 78)}, "emblem": "봄"},
    "mom": {"bg": (252, 246, 250), "ink": (52, 30, 60), "sub": (120, 96, 128), "badge": "엄마는 늦깎이 대학생", "handle": "@boxheysoo", "scale": 1.0,
            "speakers": {"mom": (150, 84, 160)}, "emblem": "맘"},
}
CARD = (255, 255, 255)

# 쇼츠/릴스/틱톡 UI가 덮는 영역을 피한다: 위 200, 아래 380, 오른쪽 140
SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT, SIDE = 200, 380, 140, 70


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def wrap(draw, text, fnt, width):
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        line = ""
        for ch in para:
            if draw.textlength(line + ch, font=fnt) > width and line:
                cut = line.rfind(" ")
                if cut > 0:
                    lines.append(line[:cut])
                    line = line[cut + 1:] + ch
                else:
                    lines.append(line)
                    line = ch
            else:
                line += ch
        lines.append(line)
    return lines


def text_block(draw, xy, text, fnt, width, fill, gap=1.35, align="left"):
    x, y = xy
    for line in wrap(draw, text, fnt, width):
        if align == "center":
            lx = x + (width - draw.textlength(line, font=fnt)) / 2
        else:
            lx = x
        draw.text((lx, y), line, font=fnt, fill=fill)
        y += int(fnt.size * gap)
    return y


def placeholder_dog(img, cx, cy, r, color):
    """실제 캐릭터시트가 나오기 전까지 쓰는 임시 강아지 얼굴."""
    d = ImageDraw.Draw(img)
    ear = tuple(max(0, c - 35) for c in color)
    d.ellipse((cx - r * 1.05, cy - r * 0.55, cx - r * 0.45, cy + r * 0.75), fill=ear)
    d.ellipse((cx + r * 0.45, cy - r * 0.55, cx + r * 1.05, cy + r * 0.75), fill=ear)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    d.ellipse((cx - r * 0.5, cy + r * 0.05, cx + r * 0.5, cy + r * 0.75), fill=(255, 240, 225))
    for ex in (-0.38, 0.38):
        d.ellipse((cx + r * ex - 14, cy - r * 0.2 - 14, cx + r * ex + 14, cy - r * 0.2 + 14), fill=INK)
        d.ellipse((cx + r * ex - 4, cy - r * 0.2 - 10, cx + r * ex + 4, cy - r * 0.2 - 2), fill=(255, 255, 255))
    d.ellipse((cx - 20, cy + r * 0.12, cx + 20, cy + r * 0.12 + 28), fill=INK)
    d.arc((cx - 34, cy + r * 0.25, cx, cy + r * 0.5), 20, 160, fill=INK, width=5)
    d.arc((cx, cy + r * 0.25, cx + 34, cy + r * 0.5), 20, 160, fill=INK, width=5)


def emblem(img, cx, cy, r, color, ch):
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    d.ellipse((cx - r * 0.82, cy - r * 0.82, cx + r * 0.82, cy + r * 0.82), outline=(255, 255, 255), width=6)
    f = font(int(r * 0.95), True)
    d.text((cx - d.textlength(ch, font=f) / 2, cy - f.size * 0.62), ch, font=f, fill=(255, 255, 255))


def draw_character(img, speaker, box, brand="choko"):
    x0, y0, x1, y1 = box
    art = ROOT / "characters" / speaker / "pose.png"
    if art.exists():
        ch = Image.open(art).convert("RGBA")
        ch.thumbnail((x1 - x0, y1 - y0))
        img.paste(ch, (x0, y1 - ch.height), ch)
    else:
        r = (x1 - x0) // 2 - 10
        if speaker in ACCENT:
            placeholder_dog(img, (x0 + x1) // 2, (y0 + y1) // 2, r, ACCENT[speaker])
        else:
            b = BRANDS[brand]
            emblem(img, (x0 + x1) // 2, (y0 + y1) // 2, r, b["speakers"][speaker], b.get("emblem", "?"))


def render(t):
    b = BRANDS[t.get("brand", "choko")]
    BG_, INK_, SUB_ = b["bg"], b["ink"], b["sub"]
    k = b["scale"]
    img = Image.new("RGB", (W, H), BG_)
    d = ImageDraw.Draw(img)
    usable = W - SIDE - SAFE_RIGHT
    accent = b["speakers"][t["speaker"]]

    # 제목
    y = SAFE_TOP + 20
    d.rounded_rectangle((SIDE - 20, y - 20, W - SAFE_RIGHT + 20, y + 40), radius=30, fill=accent)
    d.text((SIDE + 10, y - 12), t.get("badge", b["badge"]), font=font(36, True), fill=(255, 255, 255))
    y += 90
    y = text_block(d, (SIDE, y), t["title"], font(int(68 * k), True), usable, INK_, gap=1.3)
    y += 40

    # 본문 카드
    card_top = y
    card_bottom = H - SAFE_BOTTOM - 330
    d.rounded_rectangle((SIDE - 20, card_top, W - SAFE_RIGHT + 20, card_bottom), radius=36, fill=CARD)
    inner = usable - 60
    cy = card_top + 50
    if t["type"] == "list":
        n = len(t["items"])
        size = 48 if n <= 3 else 44
        for i, item in enumerate(t["items"], 1):
            d.ellipse((SIDE + 10, cy + 4, SIDE + 70, cy + 64), fill=accent)
            num = str(i)
            nf = font(38, True)
            d.text((SIDE + 40 - d.textlength(num, font=nf) / 2, cy + 8), num, font=nf, fill=(255, 255, 255))
            cy = text_block(d, (SIDE + 95, cy + 2), item, font(size), inner - 95, INK_, gap=1.3) + 34
    elif t["type"] == "one":
        text_block(d, (SIDE + 10, cy + 30), t["body"], font(int(56 * k), True), inner, INK_, gap=1.4, align="center")
    elif t["type"] == "vs":
        half = (inner - 30) // 2
        for col, (head, items, color) in enumerate(
            [(t["left_head"], t["left"], SUB_), (t["right_head"], t["right"], accent)]
        ):
            x = SIDE + 10 + col * (half + 30)
            d.rounded_rectangle((x, cy, x + half, cy + 80), radius=24, fill=color)
            hf = font(int(40 * k), True)
            d.text((x + (half - d.textlength(head, font=hf)) / 2, cy + 14), head, font=hf, fill=(255, 255, 255))
            yy = cy + 120
            for item in items:
                yy = text_block(d, (x + 10, yy), "· " + item, font(int(40 * k)), half - 20, INK_, gap=1.3) + 26
        mid = SIDE + 10 + half + 15
        d.line((mid, cy + 100, mid, card_bottom - 40), fill=(230, 220, 210), width=3)

    # 캐릭터 + 말풍선
    char_top = card_bottom + 20
    char_box = (SIDE, char_top, SIDE + 280, char_top + 280)
    draw_character(img, t["speaker"], char_box, t.get("brand", "choko"))
    bx0, by0 = SIDE + 300, char_top + 40
    bx1 = W - SAFE_RIGHT + 20
    bf = font(int(40 * k), True)
    lines = wrap(d, t["bubble"], bf, bx1 - bx0 - 60)
    by1 = by0 + 50 + len(lines) * int(bf.size * 1.35)
    d.rounded_rectangle((bx0, by0, bx1, by1), radius=40, fill=CARD, outline=accent, width=4)
    d.polygon([(bx0 + 2, by0 + 60), (bx0 - 34, by0 + 90), (bx0 + 2, by0 + 100)], fill=CARD)
    text_block(d, (bx0 + 30, by0 + 25), t["bubble"], bf, bx1 - bx0 - 60, INK_, gap=1.35)

    # 출처 + 핸들 (UI 가림 영역 바로 위)
    d.text((SIDE, H - SAFE_BOTTOM - 30), t["source"], font=font(28), fill=SUB_)
    d.text((SIDE, H - SAFE_BOTTOM + 10), b["handle"], font=font(30, True), fill=accent)
    return img


def to_video(png, mp4, brand="choko", seed=""):
    """정지 카드에 아주 느린 줌을 넣은 7초 세로 영상.
    소리: 공용 배경음악(music/manifest.json, Suno Premier)에서 브랜드에 맞는 곡. 없으면 자체 합성 음원, 그것도 없으면 무음."""
    from bgm import ffmpeg_audio_args, pick
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    track = pick(brand, seed or png.stem)
    music = ROOT / "music" / "calm-cdfg.wav"
    if track:
        audio_in, af = ffmpeg_audio_args(track, VIDEO_SECONDS)
    else:
        audio_in, af = (["-i", str(music)] if music.exists() else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]), "anull"
    frames = VIDEO_SECONDS * 30
    vf = (
        f"scale=2160:3840,zoompan=z='min(zoom+0.0003,1.04)':d={frames}"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps=30,format=yuv420p"
    )
    cmd = [
        ff, "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(png),
        *audio_in,
        "-vf", vf, "-af", af, "-t", str(VIDEO_SECONDS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
        str(mp4),
    ]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--no-video", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    topics = json.loads((ROOT / "topics.json").read_text(encoding="utf-8"))
    for t in topics:
        if args.only and t["id"] != args.only:
            continue
        png = OUT / f"{t['id']}.png"
        render(t).save(png)
        if not args.no_video:
            to_video(png, OUT / f"{t['id']}.mp4", t.get("brand", "choko"), t["id"])
        print("ok", t["id"])


if __name__ == "__main__":
    main()
