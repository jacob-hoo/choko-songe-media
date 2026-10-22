"""공용 배경음악(Suno Premier 60곡, music/manifest.json)에서 한 곡을 골라 쓰는 도구.

모든 브랜드가 같이 쓴다. 정보 쇼츠(make_cards), 쿠팡 영상(coupang/render), 초코송이 라운지가 이 모듈을 쓴다.
지이사 담당 브랜드도 manifest.json의 raw_url로 같은 곡을 쓸 수 있다(볼트 '공용 배경음악' 노트 참고).

사용:
    from bgm import pick, ffmpeg_audio_args
    track = pick("silver", seed="s006-blood-pressure")
    args = ffmpeg_audio_args(track, seconds=7)   # ffmpeg 입력 인자 + 오디오 필터
"""
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "music" / "manifest.json"

# 브랜드별 어울리는 장면. 봄날은 차분한 피아노, 엄마는 로파이 재즈, 초코송이는 셋 다.
BRAND_SCENES = {
    "silver": ["exam-night"],
    "bomnal": ["exam-night"],
    "mom": ["rain-cafe"],
    "choko": ["exam-night", "rain-cafe", "snow-night"],
}


def tracks(scenes: list[str] | None = None) -> list[dict]:
    if not MANIFEST.exists():
        return []
    items = json.loads(MANIFEST.read_text(encoding="utf-8"))["tracks"]
    return [t for t in items if not scenes or t["scene"] in scenes]


def pick(brand: str, seed: str) -> dict | None:
    """같은 seed면 항상 같은 곡. 주제마다 곡이 달라져 반복감이 줄어든다."""
    pool = tracks(BRAND_SCENES.get(brand, ["exam-night", "rain-cafe", "snow-night"]))
    if not pool:
        return None
    i = int(hashlib.md5(f"{brand}:{seed}".encode()).hexdigest(), 16) % len(pool)
    return pool[i]


def ffmpeg_audio_args(track: dict | None, seconds: float, volume: float = 1.0) -> tuple[list[str], str]:
    """(입력 인자, 오디오 필터). 곡의 35% 지점부터 seconds만큼, 앞 0.3초·뒤 0.8초 페이드."""
    if not track:
        return ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"], "anull"
    start = round(track["seconds"] * 0.35, 1)
    path = REPO / track["file"]
    fade_out = max(seconds - 0.8, 0)
    af = (f"volume={volume},afade=t=in:st=0:d=0.3,afade=t=out:st={fade_out}:d=0.8,"
          f"aresample=44100")
    return ["-ss", str(start), "-t", str(seconds), "-i", str(path)], af
