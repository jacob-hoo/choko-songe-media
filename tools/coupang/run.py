"""파이프라인 진입점: build → check → approve.

브랜드마다 하루 1편, 기존 정보 쇼츠 뒤 상품 슬롯에 붙인다.
게시는 Claude가 queue.json의 approved 항목을 Metricool로 예약한다 (making-coupang-shorts 스킬).
"""
import argparse
import csv
import html
import json
import re
import sys
from datetime import date, datetime, timedelta

from config import ROOT, BRANDS, DEDUPE_DAYS, DISCLOSURE, HISTORY_FILE, OUT_DIR, PLATFORMS, VIRTUAL_LABEL
import render
import script_gen

BANNED = [(r"!", "느낌표"), (r"—", "긴 줄표"), (r"아니라", "'~이 아니라' 반전"),
          (r"(^|\s)\S{1,4}\?\s", "짧은 자문자답"), (r"최저가|인생템|무조건", "과장 표현"), (r"방치하면|큰일 나|끝납니다", "공포 소구")]


def _history() -> dict:
    return json.loads(HISTORY_FILE.read_text()) if HISTORY_FILE.exists() else {}


def _recently_used(pid: str, day: date, hist: dict) -> bool:
    last = hist.get(pid)
    return bool(last) and (day - date.fromisoformat(last)).days < DEDUPE_DAYS


def product_no(row: dict) -> int:
    return int(re.sub(r"\D", "", row["product_id"]) or 0)


def build_caption(row: dict, s: dict, platform: str) -> str:
    # 대가성 문구는 항상 첫 줄 (공정위 추천보증 지침: 첫 부분·더보기 전 노출)
    tags = " ".join(s["hashtags"])
    kw = row.get("dm_keyword") or "링크"
    no = product_no(row)
    virtual = f"\n{VIRTUAL_LABEL}" if s.get("is_virtual") else ""
    if platform == "instagram":
        return f"{DISCLOSURE}\n\n{s['caption']}{virtual}\n\n댓글에 「{kw}」 남기시면 링크를 DM으로 보내 드려요.\n프로필 링크 {no}번에서도 볼 수 있어요.\n{tags}"
    if platform == "youtube":
        return f"{DISCLOSURE}\n\n{s['caption']}\n\n구매 링크: 채널 프로필 링크 {no}번\n{tags} #shorts"
    if platform == "threads":
        # 스레드는 질문형 글이 반응이 크다 (2026-10-20 벤치마킹: 질문 글 댓글 250개)
        return f"{DISCLOSURE}\n\n{s['threads_question']}\n\n{s['caption']}{virtual}\n{row['partner_url']}"
    return f"{DISCLOSURE}\n\n{s['caption']}{virtual}\n\n프로필 링크 {no}번에서 확인해요\n{tags}"


def cmd_build(args) -> None:
    day = date.fromisoformat(args.date)
    out = OUT_DIR / args.date
    if (out / "queue.json").exists() and not args.force:
        print(f"{args.date}: 이미 만든 큐가 있음 (다시 만들려면 --force)")
        return
    out.mkdir(parents=True, exist_ok=True)
    hist = _history()
    rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
    queue = []
    for key, brand in BRANDS.items():
        cands = [r for r in rows if r["brand"] == key and not _recently_used(r["product_id"], day, hist)]
        if not cands:
            print(f"{brand['name']}: 쓸 상품 없음 (products.csv 보충 필요)")
            continue
        row = cands[0]
        s = script_gen.generate(row, seed=day.toordinal())
        item_dir = out / row["product_id"]
        item_dir.mkdir(exist_ok=True)
        render.render_video(row, s, item_dir / "short.mp4")
        cards = render.render_carousel(row, s, item_dir)
        queue.append({
            "brand": key,
            "brand_id": brand["brand_id"],
            "brand_name": brand["name"],
            "product_id": row["product_id"],
            "name": row["name"],
            "partner_url": row["partner_url"],
            "publish_at": f"{args.date}T{brand['coupang_slot']}:00+09:00",
            "title": s["title"][:90] + " #shorts",
            "youtube_category": brand["youtube_category"],
            "video": str(item_dir / "short.mp4"),
            "carousel": [str(c) for c in cards],
            "captions": {p: build_caption(row, s, p) for p in PLATFORMS},
            "pinned_comment": f"{DISCLOSURE}\n구매 링크는 프로필 링크에 있어요.",
            "hook_type": s["hook_type"],
            "dm_keyword": row.get("dm_keyword") or "링크",
            "product_no": product_no(row),
            "inpock_title": f"{product_no(row)}. {row['name']}",
            "my_take": row["my_take"],
            "script": s,
            "approved": False,
        })
        print(f"생성: {brand['name']} · {row['name']} ({s['hook_type']} / {s['angle']})")
    (out / "queue.json").write_text(json.dumps(queue, ensure_ascii=False, indent=2))
    _write_review(out, queue)
    print(f"검수 페이지: {out / 'review.html'}")


def check(queue: list[dict], day: date) -> list[str]:
    errors, hist = [], _history()
    for q in queue:
        pid = q["product_id"]
        for p, cap in q["captions"].items():
            if not cap.startswith(DISCLOSURE):
                errors.append(f"{pid}/{p}: 대가성 문구가 첫 줄에 없음")
        if DISCLOSURE not in q["pinned_comment"]:
            errors.append(f"{pid}: 고정 댓글에 대가성 문구 없음")
        if not q["my_take"].strip():
            errors.append(f"{pid}: 운영자 한 줄(my_take) 비어 있음 - 비독창 콘텐츠 위험")
        if "EXAMPLE" in q["partner_url"]:
            errors.append(f"{pid}: 예시 링크 그대로임")
        if _recently_used(pid, day, hist):
            errors.append(f"{pid}: {DEDUPE_DAYS}일 내 게시한 상품")
        s = q["script"]
        if s.get("is_virtual") and not all(VIRTUAL_LABEL in c for c in q["captions"].values()):
            errors.append(f"{pid}: 가상 상황 표기 누락")
        text = " ".join([s["hook"], *s["points"], s["verdict"], s["title"], s["caption"], s["threads_question"], *s["carousel"]])
        for pat, label in BANNED:
            if re.search(pat, text):
                errors.append(f"{pid}: 문구 규칙 위반 ({label})")
    return errors


def cmd_check(args) -> int:
    queue = json.loads((OUT_DIR / args.date / "queue.json").read_text())
    errors = check(queue, date.fromisoformat(args.date))
    print("\n".join(errors) if errors else "통과")
    return 1 if errors else 0


def cmd_approve(args) -> int:
    path = OUT_DIR / args.date / "queue.json"
    queue = json.loads(path.read_text())
    errors = check(queue, date.fromisoformat(args.date))
    if errors:
        print("승인 불가:\n" + "\n".join(errors))
        return 1
    hist = _history()
    for q in queue:
        q["approved"] = True
        hist[q["product_id"]] = args.date
    path.write_text(json.dumps(queue, ensure_ascii=False, indent=2))
    HISTORY_FILE.write_text(json.dumps(hist, ensure_ascii=False, indent=2))
    print(f"{len(queue)}건 승인 → Metricool 예약 대기")
    return 0


def cmd_pending(args) -> int:
    """승인됐지만 아직 예약하지 않은, 게시 시각이 미래인 항목을 JSON으로 출력 (일일 루틴용)."""
    now = datetime.now().astimezone()
    items = []
    for qf in sorted(OUT_DIR.glob("*/queue.json")):
        for q in json.loads(qf.read_text()):
            if q.get("approved") and not q.get("scheduled") and datetime.fromisoformat(q["publish_at"]) > now:
                items.append({**q, "date": qf.parent.name, "media_name": f"cp-{qf.parent.name}-{q['product_id']}.mp4"})
    print(json.dumps(items, ensure_ascii=False, indent=2))
    return 0


def cmd_unapproved(args) -> int:
    """만들었지만 승인을 기다리는 큐 (보고용)."""
    for qf in sorted(OUT_DIR.glob("*/queue.json")):
        q = json.loads(qf.read_text())
        if q and not all(i.get("approved") for i in q):
            print(f"{qf.parent.name}: 승인 대기 {len(q)}건 → {qf.parent / 'review.html'}")
    return 0


def cmd_mark(args) -> int:
    """예약 결과 기록: run.py mark <날짜> <상품ID> <network>=<post_id> ..."""
    path = OUT_DIR / args.date / "queue.json"
    queue = json.loads(path.read_text())
    for q in queue:
        if q["product_id"] == args.product_id:
            q["scheduled"] = dict(kv.split("=", 1) for kv in args.posts)
    path.write_text(json.dumps(queue, ensure_ascii=False, indent=2))
    print(f"{args.date}/{args.product_id} 예약 기록")
    return 0


def _write_review(out, queue) -> None:
    cards = "".join(
        f"<section><h2>{html.escape(q['brand_name'])} · {html.escape(q['name'])} · {q['publish_at'][11:16]}</h2>"
        f"<p>훅: {html.escape(q['hook_type'])} · 자동 DM 키워드: {html.escape(q['dm_keyword'])} · 인포크 항목: {html.escape(q['inpock_title'])}</p>"
        f"<video src='{q['product_id']}/short.mp4' controls width=270></video>"
        f"<pre>{html.escape(q['captions']['instagram'])}</pre>"
        f"<p>my_take: <b>{html.escape(q['my_take'] or '비어 있음 - products.csv에 한 줄 입력 후 다시 build')}</b></p></section>"
        for q in queue)
    (out / "review.html").write_text(
        f"<!doctype html><meta charset=utf-8><title>검수 {out.name}</title>"
        f"<style>body{{font-family:sans-serif;max-width:720px;margin:24px auto;padding:0 16px}}"
        f"section{{border-bottom:1px solid #ddd;padding:16px 0}}pre{{white-space:pre-wrap;background:#f6f6f6;padding:12px}}</style>"
        f"<h1>검수 {out.name}</h1>{cards}")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--csv", default=str(ROOT / "products.csv"))
    b.add_argument("--date", default=(datetime.now() + timedelta(days=1)).date().isoformat())
    b.add_argument("--force", action="store_true")
    for name in ("check", "approve"):
        sub.add_parser(name).add_argument("date")
    sub.add_parser("pending")
    sub.add_parser("unapproved")
    m = sub.add_parser("mark")
    m.add_argument("date")
    m.add_argument("product_id")
    m.add_argument("posts", nargs="+")
    args = ap.parse_args()
    return {"build": cmd_build, "check": cmd_check, "approve": cmd_approve, "pending": cmd_pending,
            "unapproved": cmd_unapproved, "mark": cmd_mark}[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
