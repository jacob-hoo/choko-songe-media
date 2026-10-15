"""브랜드 대표 이미지: 프로필 사진(1080x1080, 원형으로 잘려도 안전)과 유튜브 배너(2560x1440, 가운데 1546x423 안전 영역).
make_cards.py 의 색·캐릭터·폰트를 그대로 써서 카드와 같은 얼굴로 맞춘다.
사용: .venv/bin/python make_brand.py  →  ../brand/<brand>/profile.png, youtube_banner.png
"""
from pathlib import Path

from PIL import Image, ImageDraw

from make_cards import ACCENT, BRANDS, INK, emblem, font, placeholder_dog

OUT = Path(__file__).parent.parent / "brand"

INFO = {
    "choko": {"name": "초코송이", "tag": "하루 한 장 · 아침 한 줄", "handle": "@choko_songe_family"},
    "silver": {"name": "봄날 수첩", "tag": "70대의 하루를 돕는 생활 정보", "handle": "@bomnal_sucheop"},
    "mom": {"name": "엄마는 늦깎이 대학생", "tag": "공부와 살림, 같이 해요", "handle": "@eomma_daehaksaeng"},
}


def mark(img, brand, cx, cy, r):
    """브랜드 상징: 초코송이는 강아지 둘, 나머지는 글자 원."""
    if brand == "choko":
        placeholder_dog(img, int(cx - r * 0.55), cy, int(r * 0.62), ACCENT["choko"])
        placeholder_dog(img, int(cx + r * 0.55), cy, int(r * 0.62), ACCENT["song-e"])
    else:
        b = BRANDS[brand]
        emblem(img, cx, cy, r, list(b["speakers"].values())[0], b["emblem"])


def profile(brand):
    b = BRANDS[brand]
    s = 1080
    img = Image.new("RGB", (s, s), b["bg"])
    # 원형으로 잘려도 안전하도록 가운데 70% 안에만 그린다
    mark(img, brand, s // 2, s // 2 + (30 if brand == "choko" else 0), 300 if brand != "choko" else 330)
    return img


def banner(brand):
    b, info = BRANDS[brand], INFO[brand]
    W, H = 2560, 1440
    img = Image.new("RGB", (W, H), b["bg"])
    d = ImageDraw.Draw(img)
    # 안전 영역(모든 기기에서 보이는 곳): 가운데 1546x423
    sx0, sy0 = (W - 1546) // 2, (H - 423) // 2
    accent = list(b["speakers"].values())[0]
    d.rectangle((0, sy0 + 423 + 40, W, sy0 + 423 + 52), fill=accent)
    r = 170
    mark(img, brand, sx0 + r + 20, H // 2, r if brand != "choko" else 190)
    tx = sx0 + 2 * r + 110 + (60 if brand == "choko" else 0)
    name_f = font(118 if len(info["name"]) <= 6 else 96, True)
    d.text((tx, H // 2 - 130), info["name"], font=name_f, fill=b["ink"])
    d.text((tx, H // 2 + 20), info["tag"], font=font(56), fill=b["sub"])
    d.text((tx, H // 2 + 105), info["handle"], font=font(44, True), fill=accent)
    return img


def main():
    for brand in INFO:
        o = OUT / brand
        o.mkdir(parents=True, exist_ok=True)
        profile(brand).save(o / "profile.png")
        banner(brand).save(o / "youtube_banner.png")
        print("ok", brand)


if __name__ == "__main__":
    main()
