"""초코송이 라운지: AI 음악 롱폼(1시간) + 쇼츠 파이프라인.

곡은 대장님이 Suno(유료 플랜)에서 만들어 내려받고, 나머지는 이 스크립트가 처리한다.
  prompts <장면>          Suno에 넣을 스타일·장면 문구 출력
  ingest <장면> <폴더>     내려받은 곡을 등록 (tracks.csv, audio/<장면>/)
  image <장면>            장면 그림이 없으면 임시 그림 생성 (art/<장면>.png)
  render <장면>           1시간 롱폼 mp4 + 설명(트랙리스트·챕터) + 썸네일
  shorts <장면> [--n 7]    곡마다 25초 세로 쇼츠
  test-tracks <장면> [--n 3] 시험용 자체 합성 곡 (파이프라인 점검용, 게시 금지)
"""
import argparse
import csv
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT.parent
TRACKS = ROOT / "tracks.csv"
AUDIO = ROOT / "audio"
ART = ROOT / "art"
OUT = ROOT / "out"
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
XFADE = 3.0  # 곡 사이 겹침(초)
CHANNEL = "초코송이 라운지"
AI_NOTE = ("음악은 AI 작곡 도구 Suno(유료 플랜)로 만든 연주곡을 골라 이어 붙였어요. (AI 생성 음악) "
           "영상 속 초코와 송이는 초코송이의 캐릭터입니다.")
FIELDS = ["track_id", "scene_id", "title", "file", "seconds", "selected", "source", "notes"]


def scenes() -> dict:
    return {s["id"]: s for s in json.loads((ROOT / "scenes.json").read_text(encoding="utf-8"))}


def rows() -> list[dict]:
    return list(csv.DictReader(open(TRACKS, encoding="utf-8")))


def save_rows(rs: list[dict]) -> None:
    with open(TRACKS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rs)


def probe(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def ts(sec: float) -> str:
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------- 명령

def cmd_prompts(a) -> None:
    s = scenes()[a.scene]
    print(f"[{s['title']}] 용도: {s['use']} / 분위기: {s['mood']}")
    print(f"Suno 스타일: {s['suno_style']}")
    print("Suno 설정: Instrumental 켜기, 곡 길이 2분30초~3분30초, 한 번에 2곡씩 생성")
    print("필요한 곡 수: 1시간 편 기준 20곡 고르기 (약 60곡 생성 후 선별)")
    print(f"장면(그림용): {s['scene']}")


def cmd_ingest(a) -> None:
    src = Path(a.folder)
    dst = AUDIO / a.scene
    dst.mkdir(parents=True, exist_ok=True)
    rs = rows()
    have = {r["file"] for r in rs}
    n = sum(1 for r in rs if r["scene_id"] == a.scene)
    for f in sorted(p for p in src.iterdir() if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".flac")):
        target = dst / f.name
        if str(target.relative_to(ROOT)) in have:
            continue
        shutil.copy2(f, target)
        n += 1
        rs.append({"track_id": f"{a.scene}-{n:02d}", "scene_id": a.scene, "title": f.stem.replace("_", " "),
                   "file": str(target.relative_to(ROOT)), "seconds": f"{probe(target):.1f}",
                   "selected": "Y", "source": a.source, "notes": ""})
        print("등록:", f.name)
    save_rows(rs)


def cmd_image(a) -> Path:
    ART.mkdir(exist_ok=True)
    p = ART / f"{a.scene}.png"
    if p.exists():
        return p
    s = scenes()[a.scene]
    c1, c2 = (tuple(c) for c in s["palette"])
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
    # 임시 캐릭터 (캐릭터시트 확정 전)
    for cx, col in ((W // 2 - 170, (150, 100, 60)), (W // 2 + 170, (235, 200, 160))):
        r = 130
        ear = tuple(max(0, v - 35) for v in col)
        d.ellipse((cx - r * 1.05, 620 - r * .55, cx - r * .45, 620 + r * .75), fill=ear)
        d.ellipse((cx + r * .45, 620 - r * .55, cx + r * 1.05, 620 + r * .75), fill=ear)
        d.ellipse((cx - r, 620 - r, cx + r, 620 + r), fill=col)
        for ex in (-.38, .38):
            d.ellipse((cx + r * ex - 12, 620 - r * .2 - 12, cx + r * ex + 12, 620 - r * .2 + 12), fill=(30, 30, 30))
        d.ellipse((cx - 16, 620 + r * .12, cx + 16, 620 + r * .12 + 22), fill=(30, 30, 30))
    f = font(FONT_R, 40)
    label = "임시 그림 · 장면 그림 확정 후 교체"
    d.text((W - d.textlength(label, font=f) - 40, H - 70), label, font=f, fill=(255, 255, 255))
    img.save(p)
    print("임시 장면 그림:", p)
    return p


def _scene_tracks(scene: str) -> list[dict]:
    ts_ = [r for r in rows() if r["scene_id"] == scene and r["selected"].upper() == "Y"]
    if not ts_:
        sys.exit(f"{scene}: 선택된 곡이 없음 (ingest 먼저)")
    return ts_


def cmd_render(a) -> None:
    s = scenes()[a.scene]
    tracks = _scene_tracks(a.scene)
    limit = a.max_minutes * 60
    picked, total = [], 0.0
    for t in tracks:
        if total >= limit:
            break
        picked.append(t)
        total += float(t["seconds"]) - (XFADE if picked[:-1] else 0)
    out = OUT / f"{date.today().isoformat()}-{a.scene}"
    out.mkdir(parents=True, exist_ok=True)
    img = cmd_image(a)

    # 1) 오디오: 곡 사이 3초 크로스페이드
    audio = out / "audio.m4a"
    ins = sum((["-i", str(ROOT / t["file"])] for t in picked), [])
    if len(picked) == 1:
        filt = "[0:a]anull[a]"
    else:
        chain, prev = [], "[0:a]"
        for i in range(1, len(picked)):
            lab = f"[x{i}]" if i < len(picked) - 1 else "[a]"
            chain.append(f"{prev}[{i}:a]acrossfade=d={XFADE}:c1=tri:c2=tri{lab}")
            prev = lab
        filt = ";".join(chain)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", filt, "-map", "[a]",
                    "-c:a", "aac", "-b:a", "192k", str(audio)], check=True)
    dur = probe(audio)

    # 2) 시작 시각과 트랙리스트
    starts, cur = [], 0.0
    for i, t in enumerate(picked):
        starts.append(cur)
        cur += float(t["seconds"]) - XFADE
    tracklist = "\n".join(f"{ts(st)} {t['title']}" for st, t in zip(starts, picked))

    # 3) 영상: 장면 그림 + 지금 곡 제목 (하단). 정지 화면이라 낮은 프레임으로 빠르게 만든다.
    draw = []
    for st, t, nxt in zip(starts, picked, starts[1:] + [dur]):
        title = t["title"].replace(":", "\\:").replace("'", "")
        draw.append(f"drawtext=fontfile={FONT_R}:text='♪ {title}':x=60:y=h-110:fontsize=40:"
                    f"fontcolor=white:shadowcolor=black@0.6:shadowx=2:shadowy=2:enable='between(t,{st:.1f},{nxt:.1f})'")
    draw.append(f"drawtext=fontfile={FONT_B}:text='{CHANNEL}':x=60:y=50:fontsize=44:fontcolor=white@0.9:"
                f"shadowcolor=black@0.5:shadowx=2:shadowy=2")
    video = out / f"{a.scene}-longform.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "2", "-i", str(img),
                    "-i", str(audio), "-vf", "scale=1920:1080," + ",".join(draw), "-r", "2",
                    "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-c:a", "copy",
                    "-shortest", "-movflags", "+faststart", str(video)], check=True)

    # 4) 설명·제목·썸네일
    title = f"{s['title']} 🎧 {s['mood']} {round(dur / 60)}분 | {s['use']}할 때 듣는 음악 | {CHANNEL}"
    desc = (f"초코와 송이의 {s['title']}.\n{s['use']}할 때 틀어 두기 좋은 {s['mood']} 플레이리스트예요.\n\n"
            f"🎵 트랙리스트\n{tracklist}\n\n{AI_NOTE}\n\n"
            f"#초코송이 #초코송이라운지 #플레이리스트 #{s['use'].split('·')[0]}음악 #{s['mood'].split()[-1]}")
    (out / "title.txt").write_text(title, encoding="utf-8")
    (out / "description.txt").write_text(desc, encoding="utf-8")
    th = Image.open(img).convert("RGB").resize((1280, 720))
    d = ImageDraw.Draw(th)
    d.rectangle([0, 520, 1280, 720], fill=(0, 0, 0))
    f1, f2 = font(FONT_B, 64), font(FONT_R, 36)
    d.text((50, 540), s["title"], font=f1, fill=(255, 255, 255))
    d.text((50, 632), f"{s['mood']} · {round(dur / 60)}분 · {CHANNEL}", font=f2, fill=(255, 220, 160))
    th.save(out / "thumbnail.jpg", quality=92)
    json.dump({"scene": a.scene, "tracks": [t["track_id"] for t in picked], "starts": starts, "duration": dur},
              open(out / "episode.json", "w"), ensure_ascii=False, indent=2)
    for t in picked:  # 사용 기록
        pass
    print(f"롱폼: {video} ({ts(dur)}, {len(picked)}곡)")
    print(f"제목: {title}")


def cmd_shorts(a) -> None:
    s = scenes()[a.scene]
    img = Image.open(cmd_image(a)).convert("RGB")
    out = OUT / f"{date.today().isoformat()}-{a.scene}" / "shorts"
    out.mkdir(parents=True, exist_ok=True)
    W, H = 1080, 1920
    for i, t in enumerate(_scene_tracks(a.scene)[: a.n], 1):
        sec = float(t["seconds"])
        start = max(0.0, sec * 0.35)
        length = min(25.0, sec - start)
        frame = Image.new("RGB", (W, H), tuple(s["palette"][0]))
        bg = img.resize((int(img.width * H / img.height), H)).filter(ImageFilter.GaussianBlur(18))
        frame.paste(bg, ((W - bg.width) // 2, 0))
        fg = img.copy()
        fg.thumbnail((W, W))
        frame.paste(fg, (0, (H - fg.height) // 2 - 120))
        d = ImageDraw.Draw(frame)
        f1, f2, f3 = font(FONT_B, 66), font(FONT_R, 44), font(FONT_R, 36)
        d.text((60, 220), s["title"], font=f1, fill=(255, 255, 255))
        d.text((60, 310), f"{s['use']}할 때 · {s['mood']}", font=f2, fill=(255, 225, 170))
        d.text((60, H - 420), f"♪ {t['title']}", font=f2, fill=(255, 255, 255))
        d.text((60, H - 340), "전체 1시간 플레이리스트는 채널에서", font=f3, fill=(235, 235, 235))
        d.text((60, H - 160), CHANNEL, font=f3, fill=(255, 255, 255))
        png = out / f"short{i:02d}.png"
        frame.save(png)
        mp4 = out / f"short{i:02d}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(png),
                        "-ss", f"{start:.1f}", "-t", f"{length:.1f}", "-i", str(ROOT / t["file"]),
                        "-af", f"afade=t=in:d=1,afade=t=out:st={length - 1.5:.1f}:d=1.5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
                        "-movflags", "+faststart", str(mp4)], check=True)
        print("쇼츠:", mp4)


def cmd_test_tracks(a) -> None:
    """파이프라인 점검용 자체 합성 곡. 게시하지 않는다."""
    tmp = ROOT / "test_audio" / a.scene
    tmp.mkdir(parents=True, exist_ok=True)
    py = TOOLS / ".venv" / "bin" / "python"
    for i in range(1, a.n + 1):
        f = tmp / f"시험곡_{i:02d}.wav"
        subprocess.run([str(py), str(TOOLS / "make_music.py"), str(f), str(40 + i * 10)], check=True,
                       stdout=subprocess.DEVNULL)
    a.folder, a.source = str(tmp), "test-synth"
    cmd_ingest(a)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prompts", "image", "render", "shorts", "test-tracks"):
        p = sub.add_parser(name)
        p.add_argument("scene")
    sub.choices["render"].add_argument("--max-minutes", type=int, default=60)
    sub.choices["shorts"].add_argument("--n", type=int, default=7)
    sub.choices["test-tracks"].add_argument("--n", type=int, default=3)
    p = sub.add_parser("ingest")
    p.add_argument("scene")
    p.add_argument("folder")
    p.add_argument("--source", default="suno-premier")
    a = ap.parse_args()
    if a.cmd not in ("ingest", "test-tracks") and a.scene not in scenes():
        sys.exit(f"없는 장면: {a.scene} (scenes.json 확인)")
    {"prompts": cmd_prompts, "ingest": cmd_ingest, "image": cmd_image, "render": cmd_render,
     "shorts": cmd_shorts, "test-tracks": cmd_test_tracks}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
