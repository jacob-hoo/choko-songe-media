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

# 주제 분위기에 맞는 장면(대장님 지시 2026-11-01). 앞 줄부터 찾고, 없으면 브랜드 기본 장면.
# 쉼·위로 = 오르골(snow-night), 살림·일상 = 로파이 재즈(rain-cafe), 제도·건강·공부 = 잔잔한 피아노(exam-night).
MOOD_SCENES = [
    ("snow-night", ["아침 한 줄", "마음", "위로", "수면", "잠들", "휴식", "고마워", "고맙", "스트레스", "명상", "외로"]),
    ("rain-cafe", ["살림", "정리", "청소", "물때", "냉장고", "주방", "욕실", "수납", "세탁", "요리", "문구", "볼펜", "습관", "밀폐", "싱크대"]),
    ("exam-night", ["연금", "검진", "건강", "혈압", "혈당", "보험", "지원", "감면", "공부", "시험", "암기", "복습", "리포트", "과제"]),
]
BRAND_SCENES = {"silver": "exam-night", "bomnal": "exam-night", "mom": "rain-cafe", "choko": "rain-cafe", "ssi": "rain-cafe", "tojung": "snow-night"}


def scene_for(brand: str, text: str = "") -> str:
    for scene, words in MOOD_SCENES:
        if any(w in text for w in words):
            return scene
    return BRAND_SCENES.get(brand, "exam-night")


def topic_text(t: dict) -> str:
    """주제의 글자를 모은다. mood에 장면 id를 넣으면 그 장면을 쓴다."""
    parts = [t.get("mood", ""), t.get("title", ""), t.get("hook", ""), t.get("badge", ""), t.get("body", "")]
    parts += t.get("items", []) + t.get("left", []) + t.get("right", [])
    return " ".join(parts)


def tracks(scenes: list[str] | None = None) -> list[dict]:
    if not MANIFEST.exists():
        return []
    items = json.loads(MANIFEST.read_text(encoding="utf-8"))["tracks"]
    return [t for t in items if not scenes or t["scene"] in scenes]


def pick(brand: str, seed: str, text: str = "") -> dict | None:
    """분위기로 장면을 고르고, 같은 seed면 항상 같은 곡. 주제마다 곡이 달라져 반복감이 줄어든다."""
    scene = next((s for s in ("exam-night", "rain-cafe", "snow-night") if s in text), None) or scene_for(brand, text)
    pool = tracks([scene])
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
