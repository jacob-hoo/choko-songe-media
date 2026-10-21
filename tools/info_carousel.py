"""정보 캐러셀: 봄날·엄마 정보 쇼츠 주제를 인스타 캐러셀(1080x1350) 5~7장으로 만든다.

캐러셀은 저장·공유가 잘 되고, 이미 올린 정보(출처 확인 완료)를 다시 쓰므로 사실 확인 부담이 없다.
구성: 1 표지 / 2~5 항목 한 장에 하나 / 요약 한 줄 / 마지막 출처 + 공유·팔로우 안내.
(2026-10-21 AI 인스타 운영 영상 7편 분석: 정보성 5~7장, 마지막 장 출처와 공유 안내)

사용: tools/.venv/bin/python tools/info_carousel.py <topic_id>   → out/carousel/<topic_id>/card_N.jpg
     tools/.venv/bin/python tools/info_carousel.py next <brand> → 아직 캐러셀로 안 만든 가장 오래된 주제
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from make_cards import BRANDS, font, wrap

ROOT = Path(__file__).resolve().parent
TOPICS = ROOT / "topics.json"
HIST = ROOT / "carousel_history.json"
OUT = ROOT / "out" / "carousel"
W, H = 1080, 1350
ENDING = {
    "silver": "부모님께 이 게시물을 보내 드리세요.\n봄날 수첩을 팔로우하면 부모님 생활 정보를 매일 받아요.",
    "mom": "저장해 두고 필요할 때 꺼내 보세요.\n공부하는 엄마의 살림·공부 루틴을 매일 나눠요.",
}


def card(b: dict, idx: int, total: int, head: str, body: str = "", big: bool = False) -> Image.Image:
    im = Image.new("RGB", (W, H), b["bg"])
    d = ImageDraw.Draw(im)
    accent = list(b["speakers"].values())[0]
    d.rectangle([0, 0, W, 14], fill=accent)
    bf = font(30, True)
    d.text((70, 60), b["badge"], font=bf, fill=accent)
    pf = font(30)
    page = f"{idx}/{total}"
    d.text((W - 70 - d.textlength(page, font=pf), 60), page, font=pf, fill=b["sub"])
    hf = font(92 if big else 72, True)
    lines = wrap(d, head, hf, W - 160)
    y = (H - len(lines) * int(hf.size * 1.3)) // 2 - (120 if body else 0)
    for line in lines:
        d.text((80, y), line, font=hf, fill=b["ink"])
        y += int(hf.size * 1.3)
    if body:
        sf = font(46)
        y += 40
        for line in wrap(d, body, sf, W - 160):
            d.text((80, y), line, font=sf, fill=b["sub"])
            y += int(sf.size * 1.45)
    hf2 = font(32)
    d.text((80, H - 100), b["handle"], font=hf2, fill=b["sub"])
    return im


def pages(t: dict) -> list[tuple[str, str, bool]]:
    title = t["title"]
    ps = [(title, "", True)]
    if t.get("items"):
        ps += [(f"{i}. {x}", "", False) for i, x in enumerate(t["items"], 1)]
    else:
        body = " ".join(p.replace("\n", " ") for p in t.get("body", "").split("\n\n") if p.strip())
        ps.append((body, "", False))  # 문장이 장마다 끊기지 않게 한 장에
    if t.get("bubble"):
        ps.append((t["bubble"], "", True))
    return ps


def build(topic_id: str) -> list[Path]:
    t = next(x for x in json.loads(TOPICS.read_text(encoding="utf-8")) if x["id"] == topic_id)
    b = BRANDS[t["brand"]]
    src = t.get("source", "")
    src = src if src.startswith("출처") else f"출처: {src}"
    ps = pages(t) + [(ENDING[t["brand"]], src, False)]
    out = OUT / topic_id
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, (head, body, big) in enumerate(ps, 1):
        p = out / f"card_{i}.jpg"
        card(b, i, len(ps), head, body, big).save(p, quality=92)
        paths.append(p)
    caption = (f"{t['title'].replace(chr(10), ' ')}\n\n"
               + ("\n".join(f"{i}. {x}" for i, x in enumerate(t.get('items', []), 1)) or t.get("body", "").replace("\n", " "))
               + f"\n\n{src}\n\n{ENDING[t['brand']]}")
    (out / "caption.txt").write_text(caption.replace("!", "."), encoding="utf-8")
    return paths


def next_topic(brand: str) -> str | None:
    hist = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {}
    for t in json.loads(TOPICS.read_text(encoding="utf-8")):
        if t.get("brand") == brand and t["id"] not in hist:
            return t["id"]
    return None


def mark(topic_id: str, post_id: str) -> None:
    hist = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {}
    hist[topic_id] = post_id
    HIST.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    if sys.argv[1] == "next":
        tid = next_topic(sys.argv[2])
        print(tid or "")
        if tid:
            print("\n".join(str(p) for p in build(tid)))
    elif sys.argv[1] == "mark":
        mark(sys.argv[2], sys.argv[3])
    else:
        print("\n".join(str(p) for p in build(sys.argv[1])))
