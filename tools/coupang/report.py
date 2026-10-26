"""쿠팡파트너스 실적 리포트(클릭·주문·취소·수수료)를 Open API로 받아 저장·요약한다.

키는 저장소 밖 ~/.config/coupang-partners.env(권한 600)에 둔다. 이 파일은 값을 출력하지 않는다.
    COUPANG_ACCESS_KEY=...
    COUPANG_SECRET_KEY=...
파트너스 리포트는 매일 15:00에 갱신되고 API는 시간당 500회까지다.

    python report.py status            # 키 파일이 있는지만 확인
    python report.py fetch --days 7    # 어제까지 N일 → out/report/<오늘>.json, 요약 출력
"""
import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import coupang_api

KEY_FILE = Path.home() / ".config" / "coupang-partners.env"
OUT = Path(__file__).resolve().parent / "out" / "report"
KINDS = ["clicks", "orders", "cancels", "commission"]


def load_keys() -> bool:
    if os.environ.get("COUPANG_ACCESS_KEY") and os.environ.get("COUPANG_SECRET_KEY"):
        return True
    if not KEY_FILE.exists():
        return False
    for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))
    return bool(os.environ.get("COUPANG_ACCESS_KEY") and os.environ.get("COUPANG_SECRET_KEY"))


def fetch_kind(kind: str, start: str, end: str) -> list[dict]:
    rows, page = [], 0
    while True:
        res = coupang_api._request("GET", f"{coupang_api.BASE}/reports/{kind}",
                                   {"startDate": start, "endDate": end, "page": page})
        if str(res.get("rCode", "0")) != "0":
            raise RuntimeError(f"{kind}: rCode={res.get('rCode')} {res.get('rMessage')}")
        data = res.get("data") or []
        rows += data
        if len(data) < 1000:
            return rows
        page += 1


def summarize(rep: dict) -> dict:
    s = {"clicks": sum(int(r.get("click", 0)) for r in rep["clicks"]),
         "orders": len(rep["orders"]), "cancels": len(rep["cancels"]),
         "gmv": sum(int(r.get("gmv", 0)) for r in rep["orders"]),
         "commission": sum(int(r.get("commission", 0)) for r in rep["commission"])}
    by_product = {}
    for r in rep["orders"]:
        k = r.get("productName", "?")
        by_product[k] = by_product.get(k, 0) + int(r.get("commission", 0))
    s["top_products"] = sorted(by_product.items(), key=lambda x: -x[1])[:5]
    by_sub = {}
    for r in rep["clicks"]:
        k = r.get("subId") or "(없음)"
        by_sub[k] = by_sub.get(k, 0) + int(r.get("click", 0))
    s["clicks_by_subid"] = by_sub
    return s


def cmd_status(_a) -> int:
    if not KEY_FILE.exists() and not os.environ.get("COUPANG_ACCESS_KEY"):
        print(f"키 없음: {KEY_FILE} 를 만들어야 한다")
        return 2
    mode = oct(KEY_FILE.stat().st_mode & 0o777) if KEY_FILE.exists() else "env"
    print("키 있음", mode, "(값은 출력하지 않음)")
    return 0


def cmd_fetch(a) -> int:
    if not load_keys():
        print(f"키 없음: {KEY_FILE}")
        return 2
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=a.days - 1)
    s, e = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
    rep = {k: fetch_kind(k, s, e) for k in KINDS}
    summary = summarize(rep)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{date.today().isoformat()}.json"
    path.write_text(json.dumps({"start": s, "end": e, "summary": summary, "raw": rep},
                               ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{s}~{e} 클릭 {summary['clicks']} · 주문 {summary['orders']} · 취소 {summary['cancels']} · "
          f"주문액 {summary['gmv']:,}원 · 수수료 {summary['commission']:,}원")
    for name, c in summary["top_products"]:
        print(f"  {c:,}원  {name}")
    print("  subId별 클릭:", summary["clicks_by_subid"])
    print("저장:", path)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    f = sub.add_parser("fetch")
    f.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    return {"status": cmd_status, "fetch": cmd_fetch}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
