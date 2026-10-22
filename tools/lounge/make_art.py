"""초코송이 라운지 장면 그림(1920x1080). art/<장면>.png(제목 있음, 롱폼용)와 art/<장면>-clean.png(제목 없음, 곡 영상용)."""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
W, H = 1920, 1080
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
TITLES = {"exam-night": ("시험 전날 밤, 공부할 때 듣는 피아노", "초코송이 라운지 · 1 hour study piano"),
          "rain-cafe": ("비 오는 날 카페 창가, 작업할 때 듣는 로파이", "초코송이 라운지 · 1 hour lofi jazz"),
          "snow-night": ("눈 오는 밤 다락방, 잠들기 전 듣는 오르골", "초코송이 라운지 · 1 hour sleep music box")}


def dogs():
    d = Image.open(REPO / "brand/choko/profile.png").convert("RGB").crop((130, 350, 950, 800)).resize((574, 315))
    probe = d.copy()
    for xy in [(0, 0), (573, 0), (0, 314), (573, 314)]:
        ImageDraw.floodfill(probe, xy, (255, 0, 255), thresh=25)
    mk = Image.new("L", d.size, 255)
    mp, pp = mk.load(), probe.load()
    for x in range(d.size[0]):
        for y in range(d.size[1]):
            if pp[x, y] == (255, 0, 255):
                mp[x, y] = 0
    return d, mk


def grad(top, bot):
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return im


def exam_night(dg, mk):
    bg = grad((18, 22, 40), (38, 36, 50))
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([360, 120, 1560, 1020], fill=170)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    bg = Image.composite(Image.new("RGB", (W, H), (255, 196, 120)), bg, glow.point(lambda v: int(v * 0.55)))
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 820, W, H], fill=(58, 40, 30)); d.rectangle([0, 812, W, 826], fill=(92, 64, 44))
    d.polygon([(1380, 300), (1500, 300), (1560, 420), (1320, 420)], fill=(230, 190, 120))
    d.rectangle([1432, 420, 1448, 800], fill=(70, 60, 55)); d.ellipse([1370, 790, 1510, 830], fill=(70, 60, 55))
    d.polygon([(520, 800), (880, 760), (900, 812), (540, 830)], fill=(245, 240, 228))
    d.polygon([(900, 812), (880, 760), (1240, 770), (1260, 820)], fill=(236, 230, 215))
    bg.paste(dg, (673, 520), mk)
    return bg


def rain_cafe(dg, mk):
    im = grad((52, 66, 88), (120, 104, 92)); d = ImageDraw.Draw(im)
    d.rectangle([260, 170, 1660, 760], fill=(70, 92, 120))
    rain = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(rain); random.seed(3)
    for _ in range(420):
        x = random.randint(260, 1660); y = random.randint(170, 740)
        rd.line([(x, y), (x - 6, y + 22)], fill=(200, 220, 240, 110), width=2)
    im.paste(rain, (0, 0), rain); d = ImageDraw.Draw(im)
    for x in (260, 960, 1660):
        d.rectangle([x - 10, 170, x + 10, 760], fill=(92, 70, 56))
    d.rectangle([250, 160, 1670, 180], fill=(92, 70, 56)); d.rectangle([0, 760, W, H], fill=(110, 80, 60))
    d.rectangle([0, 752, W, 770], fill=(140, 104, 78))
    d.rounded_rectangle([1380, 660, 1480, 760], 18, fill=(236, 228, 214)); d.ellipse([1380, 648, 1480, 680], fill=(120, 80, 56))
    im.paste(dg, (673, 445), mk)
    return im


def snow_night(dg, mk):
    im = grad((30, 36, 66), (60, 58, 90)); d = ImageDraw.Draw(im)
    d.ellipse([1240, 140, 1660, 560], fill=(58, 72, 120))
    snow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(snow); random.seed(5)
    for _ in range(160):
        x = random.randint(1255, 1645); y = random.randint(155, 545)
        if (x - 1450) ** 2 + (y - 350) ** 2 < 195 ** 2:
            sd.ellipse([x, y, x + 6, y + 6], fill=(240, 244, 255, 220))
    im.paste(snow, (0, 0), snow); d = ImageDraw.Draw(im)
    d.ellipse([1240, 140, 1660, 560], outline=(150, 120, 96), width=18)
    d.polygon([(0, 0), (700, 0), (0, 420)], fill=(44, 40, 60)); d.rectangle([0, 780, W, H], fill=(70, 58, 72))
    im.paste(dg, (673, 470), mk); d = ImageDraw.Draw(im)
    d.rounded_rectangle([560, 700, 1360, 860], 60, fill=(196, 148, 160))
    for i in range(3):
        d.text((1250 + i * 40, 420 - i * 50), "z", font=ImageFont.truetype(FB, 40 + i * 10), fill=(230, 230, 250))
    return im


def main():
    dg, mk = dogs()
    for sid, fn in {"exam-night": exam_night, "rain-cafe": rain_cafe, "snow-night": snow_night}.items():
        clean = fn(dg, mk)
        clean.save(ROOT / "art" / f"{sid}-clean.png")
        t1, t2 = TITLES[sid]
        im = clean.copy(); d = ImageDraw.Draw(im)
        d.text((80, 70), t1, font=ImageFont.truetype(FB, 50), fill=(255, 240, 220))
        d.text((82, 140), t2, font=ImageFont.truetype(FB, 30), fill=(225, 210, 190))
        im.save(ROOT / "art" / f"{sid}.png")
        print(sid)


if __name__ == "__main__":
    main()
