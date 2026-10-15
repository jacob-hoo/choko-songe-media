"""다봄(무료 운세 서비스) 홍보물 제작기.

결과:
  out/dabom/card-1..5.png  카드뉴스 5장(1080x1350, 인스타 캐러셀 4:5)
  out/dabom/promo.mp4      홍보 쇼츠(1080x1920, 장면 5개 x 3초 = 15초, 자체 합성 음악)
사용: .venv\\Scripts\\python.exe make_dabom.py
문구는 아래 SLIDES만 고치면 된다. 링크 주소가 정해지면 LINK_TEXT를 바꾼다.
"""
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

from make_cards import ACCENT, placeholder_dog

ROOT = Path(__file__).parent
OUT = ROOT / "out" / "dabom"
# 한글 폰트: 리눅스(클로드 PC)는 Noto Sans CJK(OFL, 상업 사용 무료, apt fonts-noto-cjk), 윈도우는 맑은고딕
_FONT_CANDIDATES = [
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/malgunbd.ttf"),
]
FONT, FONT_BOLD = next(((r, b) for r, b in _FONT_CANDIDATES if Path(r).exists()), _FONT_CANDIDATES[-1])

# 밤하늘 남색 + 달빛 금색: 운세 서비스의 신비로움을 살리되 무섭지 않게
NIGHT_TOP = (28, 30, 74)
NIGHT_BOTTOM = (64, 44, 110)
GOLD = (246, 205, 120)
WHITE = (250, 248, 255)
SOFT = (196, 190, 230)

LINK_TEXT = "프로필 링크에서 바로 시작"
NOTICE = "다봄의 풀이는 재미와 자기성찰을 위한 것이에요.\n의료·법률·투자 판단을 대신하지 않습니다."

SLIDES = [
    {"who": "song-e", "kicker": "점성사 초코송이, 문 열었어요", "title": "오늘, 나에게\n필요한 한마디", "body": "토정비결 · 타로 · 꿈해몽\n지금은 전부 무료", "icon": "star"},
    {"who": "choko", "kicker": "점성사 초코 · 토정비결 144괘", "title": "올해 내 흐름\n한눈에 보기", "body": "생년월일만 알려 주시면\n한 해의 흐름을 달마다 풀어 드려요", "icon": "calendar"},
    {"who": "song-e", "kicker": "점성사 송이 · 타로 78장", "title": "고민될 땐\n카드 한 장", "body": "질문을 떠올리고 한 장 뽑으면\n지금 필요한 이야기를 들려줘요", "icon": "card"},
    {"who": "choko", "kicker": "점성사 초코 · 꿈해몽 319가지", "title": "어젯밤 그 꿈,\n무슨 뜻일까?", "body": "돼지꿈, 이빨 빠지는 꿈, 물 꿈…\n자주 꾸는 꿈의 의미를 찾아보세요", "icon": "cloud"},
    {"who": "song-e", "kicker": "점성사 초코송이의 오픈 선물", "title": "가입도 무료,\n풀이도 무료", "body": "회원이 되면 새 기능 소식을\n가장 먼저 받아 보실 수 있어요", "icon": "star"},
]


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def gradient(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        r = y / (h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * r) for a, b in zip(NIGHT_TOP, NIGHT_BOTTOM)))
    return img


def stars(d, w, h, seed):
    x = seed * 7919
    for _ in range(70):
        x = (x * 1103515245 + 12345) % 2**31
        px, py = x % w, (x // w) % int(h * 0.36)
        if abs(px - w / 2) < w * 0.2 and py > h * 0.08:
            continue
        s = 1 + x % 3
        d.ellipse((px - s, py - s, px + s, py + s), fill=(255, 255, 255))


def draw_icon(d, kind, cx, cy, r):
    if kind == "moon":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD)
        d.ellipse((cx - r + r * 0.55, cy - r - r * 0.15, cx + r + r * 0.55, cy + r - r * 0.15), fill=NIGHT_TOP)
    elif kind == "calendar":
        d.rounded_rectangle((cx - r, cy - r * 0.8, cx + r, cy + r), radius=r // 5, outline=GOLD, width=10)
        d.line((cx - r, cy - r * 0.35, cx + r, cy - r * 0.35), fill=GOLD, width=10)
        for i in range(3):
            for j in range(2):
                x0 = cx - r * 0.6 + i * r * 0.5
                y0 = cy - r * 0.05 + j * r * 0.45
                d.rectangle((x0, y0, x0 + r * 0.25, y0 + r * 0.25), fill=GOLD)
    elif kind == "card":
        d.rounded_rectangle((cx - r * 0.65, cy - r, cx + r * 0.65, cy + r), radius=r // 6, fill=GOLD)
        d.rounded_rectangle((cx - r * 0.5, cy - r * 0.85, cx + r * 0.5, cy + r * 0.85), radius=r // 8, outline=NIGHT_TOP, width=6)
        star(d, cx, cy, r * 0.35, NIGHT_TOP)
    elif kind == "cloud":
        for ox, oy, rr in ((-0.45, 0.1, 0.45), (0.0, -0.15, 0.6), (0.5, 0.1, 0.45)):
            d.ellipse((cx + ox * r - rr * r, cy + oy * r - rr * r, cx + ox * r + rr * r, cy + oy * r + rr * r), fill=GOLD)
        d.rectangle((cx - r * 0.9, cy + r * 0.1, cx + r * 0.95, cy + r * 0.55), fill=GOLD)
        for i in range(3):
            d.text((cx - r * 0.2 + i * 40, cy - r * 1.3 - i * 30), "z", font=font(50 - i * 6, True), fill=SOFT)
    else:
        star(d, cx, cy, r, GOLD)


def astro_dog(img, who, cx, cy, r):
    """점성사 초코송이: 임시 강아지 얼굴 + 별무늬 마법사 모자 + 수정구슬."""
    d = ImageDraw.Draw(img)
    # 수정구슬 빛(뒤)
    bx, by, br = cx + r * 1.35, cy + r * 0.75, r * 0.5
    for k in range(6, 0, -1):
        a = k / 6
        col = tuple(int(c1 * (1 - a * 0.5) + c2 * a * 0.5) for c1, c2 in zip(NIGHT_BOTTOM, (170, 150, 255)))
        d.ellipse((bx - br - k * 8, by - br - k * 8, bx + br + k * 8, by + br + k * 8), fill=col)
    placeholder_dog(img, cx, cy, r, ACCENT[who])
    # 모자
    hat = (88, 64, 170)
    d.polygon([(cx - r * 0.95, cy - r * 0.55), (cx + r * 0.95, cy - r * 0.55), (cx + r * 0.25, cy - r * 2.1)], fill=hat)
    d.rounded_rectangle((cx - r * 1.15, cy - r * 0.7, cx + r * 1.15, cy - r * 0.45), radius=int(r * 0.12), fill=hat)
    star(d, cx - r * 0.1, cy - r * 1.15, r * 0.2, GOLD)
    star(d, cx + r * 0.35, cy - r * 1.6, r * 0.11, GOLD)
    star(d, cx - r * 0.5, cy - r * 0.8, r * 0.09, GOLD)
    # 구슬
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=(205, 195, 255))
    d.ellipse((bx - br * 0.55, by - br * 0.6, bx - br * 0.1, by - br * 0.2), fill=(250, 248, 255))
    d.rounded_rectangle((bx - br * 0.75, by + br * 0.8, bx + br * 0.75, by + br * 1.15), radius=8, fill=GOLD)


def star(d, cx, cy, r, color):
    import math
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy - rr * math.sin(a)))
    d.polygon(pts, fill=color)


def centered(d, text, y, fnt, w, fill, gap=1.3):
    for line in text.split("\n"):
        tw = d.textlength(line, font=fnt)
        d.text(((w - tw) / 2, y), line, font=fnt, fill=fill)
        y += int(fnt.size * gap)
    return y


def render(slide, i, w, h, safe_top, safe_bottom, total):
    img = gradient(w, h)
    d = ImageDraw.Draw(img)
    stars(d, w, h, i + 1)
    y = safe_top
    d.text((70, y), "다봄", font=font(54, True), fill=GOLD)
    d.text((w - 70 - d.textlength(f"{i + 1}/{total}", font=font(32)), y + 14), f"{i + 1}/{total}", font=font(32), fill=SOFT)
    icon_y = y + int(h * 0.2)
    dog_r = int(w * 0.11)
    astro_dog(img, slide["who"], w // 2 - int(w * 0.06), icon_y, dog_r)
    d = ImageDraw.Draw(img)
    draw_icon(d, slide["icon"], int(w * 0.2), icon_y - int(dog_r * 0.9), int(w * 0.045))
    y = icon_y + int(w * 0.19)
    kf = font(38, True)
    kw = d.textlength(slide["kicker"], font=kf)
    d.rounded_rectangle(((w - kw) / 2 - 28, y - 6, (w + kw) / 2 + 28, y + 56), radius=30, outline=GOLD, width=3)
    d.text(((w - kw) / 2, y), slide["kicker"], font=kf, fill=GOLD)
    y = centered(d, slide["title"], y + 100, font(80, True), w, WHITE) + 30
    centered(d, slide["body"], y, font(42), w, SOFT, gap=1.45)
    foot = h - safe_bottom
    if i == total - 1:
        bf = font(44, True)
        bw = d.textlength(LINK_TEXT, font=bf)
        d.rounded_rectangle(((w - bw) / 2 - 50, foot - 230, (w + bw) / 2 + 50, foot - 140), radius=45, fill=GOLD)
        d.text(((w - bw) / 2, foot - 215), LINK_TEXT, font=bf, fill=NIGHT_TOP)
    nf = font(26)
    lines = NOTICE.split("\n")
    ny = foot - 20 - len(lines) * 36
    for ln in lines:
        d.text(((w - d.textlength(ln, font=nf)) / 2, ny), ln, font=nf, fill=SOFT)
        ny += 36
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    total = len(SLIDES)
    frames = []
    for i, s in enumerate(SLIDES):
        render(s, i, 1080, 1350, 60, 60, total).save(OUT / f"card-{i + 1}.png")
        p = OUT / f"scene-{i + 1}.png"
        render(s, i, 1080, 1920, 230, 400, total).save(p)
        frames.append(p)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    music = ROOT / "music" / "dabom-15s.wav"
    subprocess.run([str(ROOT / ".venv" / "Scripts" / "python.exe"), str(ROOT / "make_music.py"), str(music), "15"], check=True)
    cmd = [ff, "-y", "-loglevel", "error"]
    for p in frames:
        cmd += ["-loop", "1", "-t", "3.5", "-i", str(p)]
    cmd += ["-i", str(music)]
    chain, last = [], "[0:v]"
    for k in range(1, len(frames)):
        out = f"[x{k}]"
        chain.append(f"{last}[{k}:v]xfade=transition=fade:duration=0.5:offset={k * 3}{out}")
        last = out
    chain.append(f"{last}format=yuv420p,fps=30[v]")
    cmd += ["-filter_complex", ";".join(chain), "-map", "[v]", "-map", f"{len(frames)}:a",
            "-t", "15", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            str(OUT / "promo.mp4")]
    subprocess.run(cmd, check=True)
    print("ok", OUT)


if __name__ == "__main__":
    main()
