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
        "audience": "50대 이상 부모님(특히 아버지)과, 부모님 선물을 사는 30~40대 자녀",
        "voice": "자녀가 부모님 선물을 고르는 시선. 존댓말, 짧은 문장, '~해요' 체. '부모님께 드리기 좋은', '아버지 선물'처럼 선물 맥락을 앞에 둔다.",
        "niche": "50대 이상 건강기능식품(식약처 인정 기능성만), 50대 이상 남성 생활·그루밍 선물, 생활 안전 효도템",
        "hashtags": ["#봄날수첩", "#부모님선물", "#아버지선물", "#효도템"],
        "coupang_slot": "21:00",
        "youtube_category": "HOWTO_STYLE",
    },
    "mom": {
        "brand_id": "7435751",
        "name": "엄마는 늦깎이 대학생",
        "audience": "공부와 살림을 같이 하는 40대 주부",
        "voice": "다정한 1인칭 엄마 화자, '~해요' 체, 이모지 1개 이내.",
        "niche": "특이한 학용품, 주방 정리, 청소 도구",
        "hashtags": ["#엄마는늦깎이대학생", "#주방정리", "#청소템", "#문구추천"],
        "coupang_slot": "21:30",
        "youtube_category": "HOWTO_STYLE",
    },
}

YOUTUBE_DAILY_CAP = 6  # 채널당 하루 업로드 상한 (새 채널은 9~10개에서 막힘, 2026-10-16 확인)
# 쿠팡 상품 게시는 인스타 중심 (프로필 링크·댓글 자동 DM이 0팔로워부터 작동, 쇼츠 설명란 링크는 클릭 불가).
# 유튜브는 업로드 한도를 정보 쇼츠에 남겨 두려고 기본에서 뺀다.
PLATFORMS = ["instagram", "threads", "tiktok"]
VIRTUAL_LABEL = "영상 속 대화는 가상 상황입니다."
# 댓글 키워드 자동 DM이 설정되기 전에는 "댓글 → DM" 안내를 쓰지 않고 "프로필 링크 n번"으로 안내한다.
DM_ENABLED = False
# 건강기능식품: 식약처 인정 기능성 문구만 쓰고, 이 고지를 캡션과 마지막 장에 넣는다 (건강기능식품법 표시·광고 기준).
HEALTH_CATEGORY = "건강기능식품"
HEALTH_NOTICE = "건강기능식품이며, 질병의 예방 및 치료를 위한 의약품이 아닙니다. 제품 포장의 섭취 방법과 주의사항을 확인하세요."
HEALTH_BANNED = r"치료|예방|완치|특효|낫|혈압을? ?낮|당뇨|암|약 대신|부작용 ?없|100%|기적"

# 렌더링
W, H = 1080, 1920
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
SCENE_SEC = 3.0
BG = (250, 246, 238)
INK = (24, 24, 27)
ACCENT = (232, 80, 41)

CLAUDE_MODEL = "claude-opus-5-5"
