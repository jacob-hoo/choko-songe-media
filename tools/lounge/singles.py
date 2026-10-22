"""곡 하나 = 영상 하나. 초코송이 채널에 60곡을 순서대로 공개하기 위한 렌더러와 공개 대기열.

유튜브 '음악' 카테고리로 공개하면 유튜브 뮤직에서도 검색·재생된다(대장님 2026-10-22 지시).
순서: 피아노(exam-night) 20곡 → 로파이(rain-cafe) 20곡 → 오르골(snow-night) 20곡.
하루 3곡(14:00·20:00·22:00), 롱폼 공개일은 2곡(20:00·22:00). 곡 쇼츠는 유튜브 하루 6개 한도 때문에 올리지 않는다(대장님 2026-10-23 "하루 3곡씩").

    python singles.py render            # out/singles/<track_id>.mp4 60편 (이미 있으면 건너뜀)
    python singles.py queue             # release_queue.json 생성(없을 때만)
    python singles.py next [--days 7]   # 앞으로 예약할 항목 JSON (루틴이 Metricool 예약에 사용)
    python singles.py mark <track_id> single=<post_id> short=<post_id>
"""
import argparse
import csv
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out" / "singles"
QUEUE = ROOT / "release_queue.json"
ORDER = ["exam-night", "rain-cafe", "snow-night"]
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
REL = "https://github.com/jacob-hoo/choko-songe-media/releases/download/lounge-singles"
SCENE_KO = {"exam-night": ("잔잔한 피아노", "공부할 때"), "rain-cafe": ("로파이 재즈", "작업할 때"),
            "snow-night": ("오르골·앰비언트", "잠들기 전")}
AI_NOTE = "음악은 AI 작곡 도구 Suno(유료 플랜)로 만든 연주곡입니다. (AI 생성 음악)"


def tracks() -> list[dict]:
    rows = [r for r in csv.DictReader(open(ROOT / "tracks.csv", encoding="utf-8")) if r["selected"].upper() == "Y"]
    return sorted(rows, key=lambda r: (ORDER.index(r["scene_id"]), r["track_id"]))


def frame(t: dict) -> Image.Image:
    img = Image.open(ROOT / "art" / f"{t['scene_id']}-clean.png").convert("RGB").resize((1920, 1080))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 900, 1920, 1080], fill=(0, 0, 0, 170))
    d.text((80, 918), t["title"], font=ImageFont.truetype(FONT_B, 64), fill=(255, 255, 255))
    mood, use = SCENE_KO[t["scene_id"]]
    d.text((82, 1006), f"{mood} · {use} · 초코송이 라운지", font=ImageFont.truetype(FONT_R, 36), fill=(255, 228, 190))
    return img


def cmd_render(_a) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for t in tracks():
        mp4 = OUT / f"{t['track_id']}.mp4"
        if mp4.exists():
            continue
        png = OUT / f"{t['track_id']}.png"
        frame(t).save(png)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "2", "-i", str(png),
                        "-i", str(ROOT / t["file"]), "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                        "-r", "2", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(mp4)],
                       check=True)
        print("곡 영상:", mp4.name)


def cmd_queue(a) -> None:
    if QUEUE.exists():
        print("이미 있음:", QUEUE)
        return
    start = date.fromisoformat(a.start)
    items = []
    for i, t in enumerate(tracks()):
        mood, use = SCENE_KO[t["scene_id"]]
        items.append({
            "track_id": t["track_id"], "title": t["title"], "scene": t["scene_id"],
            "date": (start + timedelta(days=i)).isoformat(),
            "single_url": f"{REL}/{t['track_id']}.mp4",
            "short_url": f"{REL}/{t['track_id']}-short.mp4",
            "yt_title": f"{t['title']} | {mood} · {use} 듣는 음악 | 초코송이 라운지",
            "description": f"{t['title']}\n{use} 틀어 두기 좋은 {mood} 연주곡이에요.\n\n{AI_NOTE}\n\n#초코송이 #초코송이라운지 #연주곡",
            "single": None, "short": None,
        })
    QUEUE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(len(items), "곡, 마지막", items[-1]["date"])


def cmd_next(a) -> None:
    items = json.loads(QUEUE.read_text(encoding="utf-8"))
    until = (date.today() + timedelta(days=a.days)).isoformat()
    today = date.today().isoformat()
    print(json.dumps([x for x in items if today <= x["date"] <= until and not x["single"]],
                     ensure_ascii=False, indent=2))


def cmd_mark(a) -> None:
    items = json.loads(QUEUE.read_text(encoding="utf-8"))
    kv = dict(p.split("=", 1) for p in a.posts)
    for x in items:
        if x["track_id"] == a.track_id:
            x.update({k: v for k, v in kv.items() if k in ("single", "short")})
    QUEUE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("render")
    q = sub.add_parser("queue")
    q.add_argument("--start", default=(date.today() + timedelta(days=1)).isoformat())
    n = sub.add_parser("next")
    n.add_argument("--days", type=int, default=7)
    m = sub.add_parser("mark")
    m.add_argument("track_id")
    m.add_argument("posts", nargs="+")
    a = ap.parse_args()
    {"render": cmd_render, "queue": cmd_queue, "next": cmd_next, "mark": cmd_mark}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
