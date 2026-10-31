"""상품 한 개 → 쇼츠 대본·캡션 (Claude, 키가 없으면 템플릿).

hooks.md(성과 기반 훅 라이브러리)를 매번 프롬프트에 넣는다.
주간 최적화 스킬이 hooks.md를 고치면 다음 대본부터 바로 반영된다.
"""
import json
import os
import random

from config import BRANDS, CLAUDE_MODEL, ROOT

HOOKS_FILE = ROOT / "hooks.md"
ANGLES = ["지난 정보 영상의 실천 도구", "부모님 집 점검", "이 가격에 이 기능", "맞지 않는 사람", "고르는 기준 3가지", "시간 절약"]

SCHEMA = {
    "type": "object",
    "properties": {
        "hook_type": {"type": "string", "description": "hooks.md에서 고른 훅 유형 이름"},
        "is_virtual": {"type": "boolean", "description": "가상 상황(썰) 형식이면 true"},
        "hook": {"type": "string", "description": "첫 1초 자막, 14자 이내"},
        "points": {"type": "array", "items": {"type": "string"}, "description": "장면 자막 3개, 각 16자 이내"},
        "verdict": {"type": "string", "description": "맞는 사람과 맞지 않는 사람 한 줄, 22자 이내"},
        "title": {"type": "string", "description": "쇼츠 제목, 40자 이내, #shorts 제외"},
        "caption": {"type": "string", "description": "본문 3~5줄, 대가성 문구와 해시태그 제외"},
        "threads_question": {"type": "string", "description": "스레드 첫 줄용 질문 한 문장. 시청자 경험을 묻는다, 40자 이내"},
        "carousel": {"type": "array", "items": {"type": "string"}, "description": "인스타 캐러셀 7장 문구, 각 24자 이내"},
    },
    "required": ["hook_type", "is_virtual", "hook", "points", "verdict", "title", "caption", "threads_question", "carousel"],
    "additionalProperties": False,
}

PROMPT = """너는 「{brand}」 채널의 작가다. 시청자: {audience}. 말투: {voice}
이 채널은 매일 생활 정보 쇼츠를 올리고, 하루 한 편만 그 정보를 실천할 도구를 소개한다.
아래 상품으로 15초 세로 영상 대본을 써라.

상품: {name} / {price}원 (분류: {category})
특징: {features}
연계 정보 영상: {linked_topic}
이번 각도: {angle}
운영자 한 줄 의견: {my_take}
실제 리뷰 근거: {review_notes}

<훅 라이브러리>
{hooks}
</훅 라이브러리>

규칙:
- 훅 라이브러리의 '잘 된 유형'을 우선 쓰고, '피할 유형'은 쓰지 않는다. 고른 유형 이름을 hook_type에 적는다.
- 정보가 먼저, 상품은 그 정보를 실천하는 도구로 나온다. 첫 장면부터 상품 자랑을 하지 않는다.
- 원인 반전형·리뷰 숫자형 훅은 '실제 리뷰 근거'에 있는 문구와 숫자만 쓴다. 근거가 없으면 그 유형을 고르지 않는다.
- 특징에 없는 스펙, 효능, 의학적 효과를 지어내지 않는다. 공포 소구("방치하면 끝") 금지. "최저가", "인생템", "무조건"을 쓰지 않는다.
- 맞지 않는 사람이나 아쉬운 점을 한 가지 넣는다.
- 운영자 의견이 있으면 verdict나 points에 녹인다.
- 문구 규칙: 느낌표 금지, 긴 줄표 금지, "~이 아니라 ~다" 식 반전 금지, "결과? ~" 식 자문자답 금지.
- 가상 상황(썰) 형식을 쓰면 is_virtual=true. 구매·사용 경험을 사실처럼 지어내지 않는다 (예: "어머니도 사셨대요" 금지).
- threads_question은 정답이 여러 개인 경험 질문으로 쓴다 (예: "부모님 댁 욕실, 미끄럼 대비 뭐 해 두셨어요"). 상품을 묻지 않는다.
- 상품 분류가 '건강기능식품'이면: 특징에 적힌 식약처 인정 기능성 문구만 그대로 쓴다. 질병 이름, 예방, 치료, 개선 체험, '약 대신'을 쓰지 않는다. 섭취 후기를 지어내지 않는다.
- 봄날 수첩은 부모님 선물을 고르는 자녀에게 말한다("아버지께 드리기 좋은", "부모님 댁에"). 엄마 계정은 직접 쓰는 주부에게 말한다.
- 마지막 장면은 댓글 키워드 안내다: 댓글에 「{dm_keyword}」 남기면 링크를 DM으로 보내 드린다.
"""


def _hooks() -> str:
    return HOOKS_FILE.read_text(encoding="utf-8") if HOOKS_FILE.exists() else "(아직 없음)"


def _template(row: dict, angle: str) -> dict:
    feats = [f for f in row["features"].split("|") if f] or ["사용 편의성", "가격", "보관"]
    price = int(row["price"]) if row["price"].isdigit() else 0
    topic = row.get("linked_topic") or row["name"]
    # 첫 문장이 매번 같으면 넘겨진다. 상품마다 다른 문장을 고르되 사실만 쓴다("어제 영상"처럼 날짜를 단정하지 않는다).
    t = row.get("linked_topic", "")
    hooks = {"건강기능식품": ["부모님 선물, 이 기준으로", "부모님 영양제 고르는 기준"],
             "남성선물": ["아버지 선물 고르는 기준", "아버지께 드리기 좋은 것"],
             "공부템": ["책상 위에 하나 두면", "공부 시간 지키는 도구"],
             "특이한문구": ["책상 위에 하나 두면", "필통에 하나 넣어 두면"],
             "주방정리": ["주방 정리, 이 기준으로", "싱크대 아래 정리 기준"],
             "청소": ["청소 도구 고를 때 볼 점", "청소 도구, 이것부터 봐요"],
             }.get(row["category"], ["부모님 댁에 두면 좋은 것"] if row["brand"] == "bomnal" else ["살림 도구, 이것부터 봐요"])
    if t and len(t) <= 12:
        hooks = [f"{t}, 이걸로 해요"]
    return {
        "hook_type": "연계 정보 되짚기",
        "is_virtual": False,
        "hook": random.Random(row["product_id"]).choice(hooks),
        "points": (feats + ["상세 페이지에서 크기 확인"] * 3)[:3],
        "verdict": row["my_take"] or "설치가 어려우면 자녀와 같이 해요",
        "threads_question": f"{topic}, 다들 어떻게 하고 계세요",
        "title": f"{topic}, 이렇게 실천해요 {row['name']}",
        "caption": f"{topic}\n실천할 때 쓰기 좋은 제품을 정리했어요. {row['name']}\n핵심: {', '.join(feats[:3])}",
        "carousel": [topic, row["name"], *feats[:3], f"가격 {price:,}원", "자세한 링크는 프로필에서"],
    }


def generate(row: dict, seed: int = 0) -> dict:
    brand = BRANDS[row["brand"]]
    angle = random.Random(f"{row['product_id']}-{seed}").choice(ANGLES)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        script = _template(row, angle)
    else:
        import anthropic

        client = anthropic.Anthropic()
        resp = client.beta.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": PROMPT.format(
                brand=brand["name"], audience=brand["audience"], voice=brand["voice"],
                name=row["name"], price=row["price"], category=row.get("category", ""),
                features=row["features"].replace("|", ", ") or "(없음)",
                linked_topic=row.get("linked_topic") or "(없음)",
                angle=angle, my_take=row["my_take"] or "(없음)", hooks=_hooks(),
                dm_keyword=row.get("dm_keyword") or "링크",
                review_notes=row.get("review_notes") or "(없음)")}],
        )
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"대본 생성 거절: {row['product_id']}")
        script = json.loads(next(b.text for b in resp.content if b.type == "text"))
    script["angle"] = angle
    script["hashtags"] = brand["hashtags"] + [f"#{row['category']}"]
    return script
