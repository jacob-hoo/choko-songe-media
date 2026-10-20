"""공통 설정."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "out"
HISTORY_FILE = ROOT / "history.json"  # 게시한 상품 기록 (7일 내 중복 방지)

DISCLOSURE = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
DISCLOSURE_SHORT = "광고 · 쿠팡파트너스 수수료 제공"
DEDUPE_DAYS = 7

# 기존 매일 게시 브랜드 (Metricool 제이콥 계정). mrjacobhoo(7204756)는 GPT 담당이라 넣지 않는다.
# coupang_slot: 기존 정보 쇼츠 3편(오전·오후·저녁) 뒤에 붙는 상품 슬롯. 브랜드당 하루 1편.
BRANDS = {
    "bomnal": {
        "brand_id": "7435746",
        "name": "봄날 수첩",
        "audience": "70대 부모님과 그 자녀",
        "voice": "존댓말, 짧은 문장, 큰 글씨로 읽히는 쉬운 단어. '~해요' 체.",
        "niche": "효도템: 낙상 예방, 생활 안전, 건강 관리 보조, 스마트폰 보조",
        "hashtags": ["#봄날수첩", "#효도템", "#부모님선물", "#70대"],
        "coupang_slot": "21:00",
        "youtube_category": "HOWTO_STYLE",
    },
    "mom": {
        "brand_id": "7435751",
        "name": "엄마는 늦깎이 대학생",
        "audience": "공부와 살림을 같이 하는 40대 주부",
        "voice": "다정한 1인칭 엄마 화자, '~해요' 체, 이모지 1개 이내.",
        "niche": "살림템·공부템: 정리 용기, 타이머, 독서대, 주방 시간 절약",
        "hashtags": ["#엄마는늦깎이대학생", "#살림템", "#공부템", "#40대주부"],
        "coupang_slot": "21:30",
        "youtube_category": "HOWTO_STYLE",
    },
}

YOUTUBE_DAILY_CAP = 6  # 채널당 하루 업로드 상한 (새 채널은 9~10개에서 막힘, 2026-10-16 확인)
# 쿠팡 상품 게시는 인스타 중심 (프로필 링크·댓글 자동 DM이 0팔로워부터 작동, 쇼츠 설명란 링크는 클릭 불가).
# 유튜브는 업로드 한도를 정보 쇼츠에 남겨 두려고 기본에서 뺀다.
PLATFORMS = ["instagram", "threads", "tiktok"]
VIRTUAL_LABEL = "영상 속 대화는 가상 상황입니다."

# 렌더링
W, H = 1080, 1920
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
SCENE_SEC = 3.0
BG = (250, 246, 238)
INK = (24, 24, 27)
ACCENT = (232, 80, 41)

CLAUDE_MODEL = "claude-opus-5-5"
