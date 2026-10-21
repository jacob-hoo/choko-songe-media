"""스레드 질문형 글: 봄날·엄마 정보 쇼츠 주제를 대화형 텍스트 글로 바꾼다.

스레드는 링크가 눌리고 질문 글의 반응이 크다(2026-10-20 벤치마킹: 질문 글 댓글 250개).
브랜드마다 하루 1편 추가한다. 상품 링크는 넣지 않는다(상품 글 비율을 지키기 위해).

사용: tools/.venv/bin/python tools/threads_daily.py <날짜>
  → tools/threads_out/<날짜>.json (Claude가 Metricool에 스레드 전용으로 예약)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOPICS = ROOT / "topics.json"
HIST = ROOT / "threads_history.json"
OUT = ROOT / "threads_out"

BRANDS = {
    "silver": {"blog": "7435746", "time": "11:30", "prefix": "s",
               "follow": "봄날 수첩을 팔로우하면 부모님 생활 정보를 매일 3개씩 받아요."},
    "mom": {"blog": "7435751", "time": "22:00", "prefix": "h",
            "follow": "늦깎이 대학생 엄마의 공부·살림 루틴을 매일 나눠요."},
}


def question(t: dict) -> str:
    title = t["title"].replace("\n", " ").strip()
    if t.get("type") == "list":
        return f"{title}\n이 중에 몇 개나 하고 계세요?"
    return f"{title}\n알고 계셨어요?"


def body(t: dict) -> str:
    if t.get("items"):
        return "\n".join(f"{i}. {x}" for i, x in enumerate(t["items"], 1))
    return " ".join(t.get("body", "").replace("\n\n", "\n").split("\n"))


def build(day: str) -> list[dict]:
    topics = json.loads(TOPICS.read_text(encoding="utf-8"))
    hist = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {}
    posts = []
    for key, b in BRANDS.items():
        cands = [t for t in topics if t.get("brand") == key and t["id"].startswith(b["prefix"]) and t["id"] not in hist]
        if not cands:
            continue
        t = cands[0]  # 오래된 주제부터 (이미 게시된 쇼츠라 사실 확인이 끝난 것)
        src = t.get("source", "")
        src = src if src.startswith("출처") else f"출처: {src}"
        text = f"{question(t)}\n\n{body(t)}\n\n{t.get('bubble', '')}\n\n{src}\n\n{b['follow']}"
        text = text.replace("!", ".").replace("—", ",")  # 문구 규칙: 느낌표·긴 줄표 금지
        posts.append({"topic_id": t["id"], "blog_id": b["blog"], "publish_at": f"{day}T{b['time']}:00+09:00",
                      "text": "\n".join(line.rstrip() for line in text.strip().split("\n"))})
    return posts


def main() -> int:
    day = sys.argv[1]
    OUT.mkdir(exist_ok=True)
    posts = build(day)
    (OUT / f"{day}.json").write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    for p in posts:
        print(p["publish_at"], p["topic_id"], len(p["text"]), "자")
    return 0


def mark(topic_id: str, post_id: str) -> None:
    hist = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {}
    hist[topic_id] = post_id
    HIST.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "mark":
        mark(sys.argv[2], sys.argv[3])
        sys.exit(0)
    sys.exit(main())
