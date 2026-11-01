"""매일 성과 기록을 시험군별로 집계하고 이상 신호를 알린다.

입력: coupang/out/metrics/<날짜>.json (루틴이 Metricool 응답 행을 그대로 저장)
    {"silver"|"mom"|"choko": {"ig": [[IGRE02, IGRE03, IGRE23, IGRE24, IGRE28], ...],
                              "tk": [[TKPO02, TKPO05, TKPO07], ...],
                              "th": [[THPO02, THPO03, THPO08], ...], "yt": [[YTVP02, YTVP17, YTVP06], ...],
                              "ev": [[IGEV01, TKEV07, THEV01, YTEV01, 날짜], ...]}}
    python track.py                # 가장 최근 파일 요약 출력
    python track.py --file a.json
시각은 Metricool이 주는 UTC. null은 0으로 바꾸지 않고 평균에서 뺀다.
"""
import argparse
import json
import re
from pathlib import Path
from statistics import mean, median

DIR = Path(__file__).resolve().parent / "coupang" / "out" / "metrics"
# 첫 장면 시험: 초코송이는 11/02 08:00 KST 게시분부터 움직이는 장면, 봄날·엄마는 질문 장면 유지.
TEST_START = "20261101"
NAMES = {"silver": "봄날", "mom": "엄마", "choko": "초코"}
AD = "쿠팡 파트너스"
LOW_VIEW = 5
HOSTS = {**NAMES, "ssi": "씨부엉", "tojung": "토정"}
WHO = {"C": "클이사", "G": "지이사"}


def nums(rows, i):
    return [float(r[i]) for r in rows if r[i] is not None]


def line(label, rows):
    if not rows:
        return f"{label}: 0편"
    rate, watch, views = nums(rows, 4), nums(rows, 3), nums(rows, 2)
    fmt = lambda v, u: f"{mean(v):.1f}{u}" if v else "null"
    return f"{label}: {len(rows)}편 · 3초 {fmt(rate, '%')} · 평균 시청 {fmt(watch, '초')} · 조회 {fmt(views, '')}"


def report(data):
    out, alerts = [], []
    for b, name in NAMES.items():
        d = data.get(b) or {}
        ig = [r for r in d.get("ig", []) if str(r[0]) >= TEST_START + "150000"]
        info = [r for r in ig if AD not in (r[1] or "")]
        ads = [r for r in ig if AD in (r[1] or "")]
        arm = "움직임" if b == "choko" else "질문"
        out.append(line(f"{name} 인스타 정보({arm})", info))
        if ads:
            out.append(line(f"{name} 인스타 쿠팡", ads))
        tk = d.get("tk", [])
        views = nums(tk, 2)
        if views:
            top = max((r for r in tk if r[2] is not None), key=lambda r: float(r[2]))
            out.append(f"{name} 틱톡: {len(tk)}편 · 평균 {mean(views):.0f} · 최고 {float(top[2]):.0f} ({(top[1] or '')[:24]})")
        low = [r for r in tk if r[2] is not None and float(r[2]) < LOW_VIEW and str(r[0])[:8] < max(str(x[0])[:8] for x in tk)]
        if len(low) >= 3:
            alerts.append(f"{name} 틱톡 조회 {LOW_VIEW}회 미만 {len(low)}편")
        ev = sorted(d.get("ev", []), key=lambda r: str(r[-1]))
        ev = [r for r in ev if any(v is not None for v in r[:4])]
        if ev:
            cur = ev[-1]
            out.append(f"{name} 팔로워 인스타 {cur[0]} · 틱톡 {cur[1]} · 스레드 {cur[2]} · 유튜브 {cur[3]} ({cur[-1]})")
            if len(ev) > 1:
                for i, n in enumerate(["인스타", "틱톡", "스레드", "유튜브"]):
                    a, c = ev[-2][i], cur[i]
                    if a is not None and c is not None and float(c) - float(a) >= 20:
                        alerts.append(f"{name} {n} 팔로워 하루 +{float(c) - float(a):.0f}, 출처 확인")
        else:
            alerts.append(f"{name} 팔로워 값 없음")
    return out, alerts


def cross(data):
    """교차 운영: 캡션 끝(유튜브는 제목 끝)의 by C·by G로 나눠 계정·플랫폼별로 비교한다. 묶음 비교다."""
    out = []
    for host, name in HOSTS.items():
        d = data.get(host) or {}
        for key, net in (("ig", "인스타"), ("tk", "틱톡"), ("th", "스레드"), ("yt", "유튜브")):
            rows = d.get(key, [])
            by = {w: [r for r in rows if re.search(rf"by {w}\s*$", r[1] or "")] for w in "CG"}
            if not by["C"] and not by["G"]:
                continue
            parts = []
            for w in "CG":
                v = nums(by[w], 2)
                parts.append(f"{WHO[w]} {len(by[w])}편 중앙값 {median(v):.0f}" if v else f"{WHO[w]} {len(by[w])}편 값 없음")
            out.append(f"교차 {name} {net}: " + " / ".join(parts))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    a = ap.parse_args()
    files = sorted(DIR.glob("*.json"))
    path = Path(a.file) if a.file else (files[-1] if files else None)
    if not path:
        print("기록 없음")
        return 2
    data = json.loads(path.read_text(encoding="utf-8"))
    out, alerts = report(data)
    out += cross(data)
    print(f"[{path.stem}]")
    print("\n".join("- " + x for x in out))
    print("경고: " + ("; ".join(alerts) if alerts else "없음"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
