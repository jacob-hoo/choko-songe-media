#!/usr/bin/env bash
# 매일 쇼츠 루틴(대장님 승인 2026-10-16: 브랜드별 하루 3개 자동 게시, 결과만 보고).
# 클라우드 예약 작업이 조직 정책(session_gate_denied)으로 막혀 클로드 PC 로컬 타이머로 돌린다.
# systemd --user: shorts-routine.timer (매일 09:47 KST, 꺼져 있었으면 켜질 때 실행)
set -uo pipefail
LOG_DIR="$HOME/.local/state/shorts-routine"; mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/$(date +%F).log"
cd "$HOME/choko-songe-media"

PROMPT=$(cat <<'P'
[매일 쇼츠 루틴 — 대장님 승인(2026-10-16): 자동 게시, 결과만 보고]
~/.claude/skills/posting-choko-songe-shorts/SKILL.md 를 먼저 읽고 그 절차대로 '내일'(KST) 분량만 만든다.
- 브랜드별 하루 3개. Metricool: 초코송이 7435740(08:00 아침 한 줄, 12:00·18:00 하루 한 장), 봄날 수첩 7435746(09·13·19시), 엄마는 늦깎이 대학생 7435751(10·14·20시). 7204756·7435778은 손대지 않는다.
- 먼저 getScheduledPosts로 내일 예약을 보고 빈 슬롯만 채운다(재게시용 유튜브 단독 예약은 슬롯으로 세지 않는다).
- 어제·오늘 게시분에 ERROR가 있으면 그 플랫폼만 20:30·21:30 등 빈 시간에 재예약한다(유튜브는 채널당 하루 6개 이하).
- 작업: tools/topics.json(CRLF; python json indent=2, "\n"→"\r\n", 끝 줄바꿈 없음) 추가 → tools/.venv/bin/python tools/make_cards.py --only <id> → 카드 PNG 직접 열어 검수 → mp4를 저장소 루트에 복사, git commit(끝줄 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')·push → raw.githubusercontent.com 200·크기 일치 확인 → createScheduledPost(videoCoverMilliseconds 0, providers youtube·instagram REEL·tiktok·threads, 응답 시각 확인).
- 출처가 분명한 사실만. 기존 주제와 겹치지 않게.
- 마지막 출력은 정확히 3줄: "만든 것: …" / "실패·재예약: …" / "막힌 것: …(없으면 없음)".
P
)

{
  echo "=== $(date '+%F %T') 시작"
  timeout 3600 "$HOME/.local/bin/claude" -p "$PROMPT" \
    --permission-mode auto \
    --allowedTools "Read,Write,Edit,Glob,Grep,Bash,mcp__claude_ai_Metricool_Social_Media_Management__getScheduledPosts,mcp__claude_ai_Metricool_Social_Media_Management__createScheduledPost" \
    --output-format text
  echo "=== $(date '+%F %T') 끝 (exit $?)"
} >"$LOG" 2>&1

# 공용 볼트 일지(50_일지/오늘.md, '## 클이사' 아래)에 같은 결과를 남긴다. 동기화는 vault-sync.timer 가 한다.
python3 - "$SUMMARY" <<'PY' >>"$LOG" 2>&1
import sys, datetime, pathlib, re
d = datetime.date.today().isoformat()
f = pathlib.Path.home() / "NODE-JUN-Vault" / "50_일지" / f"{d}.md"
f.parent.mkdir(parents=True, exist_ok=True)
if not f.exists():
    f.write_text(f"# {d}\n\n## 클이사\n\n## 지이사\n\n## 키미사\n\n[[미처리 업무]] · [[전체 목차]]\n", encoding="utf-8")
s = f.read_text(encoding="utf-8")
entry = "- 쇼츠 루틴(09:47): " + " / ".join(l.strip() for l in sys.argv[1].splitlines() if l.strip()) + " → [[쇼츠 운영]]\n"
if "## 클이사" not in s:
    s = s.rstrip("\n") + "\n\n## 클이사\n"
m = re.search(r"## 클이사\n(.*?)(?=\n## |\n\[\[|\Z)", s, re.S)
pos = m.end(1) if m else len(s)
body = s[:pos].rstrip("\n") + "\n" + entry
s = body + "\n" + s[pos:].lstrip("\n") if s[pos:].strip() else body
f.write_text(s if s.endswith("\n") else s + "\n", encoding="utf-8")
print("vault log ok", f)
PY

# 지휘통제실로 결과 보고(클이사 봇). 토큰은 출력하지 않는다.
SUMMARY=$(grep -E '^(만든 것|실패·재예약|막힌 것):' "$LOG" | tail -3)
[ -n "$SUMMARY" ] || SUMMARY="루틴이 정상 보고를 남기지 못했습니다. 로그: $LOG"
TOKEN=$(grep -E '^DISCORD_BOT_TOKEN=' "$HOME/.hermes/.env" | cut -d= -f2- | tr -d '"'"'")
CH=1554055714505236521
python3 - "$SUMMARY" <<'PY' | curl -s -o /dev/null -w '%{http_code}\n' -X POST \
  -H "Authorization: Bot $TOKEN" -H 'Content-Type: application/json' \
  --data-binary @- "https://discord.com/api/v10/channels/$CH/messages" >>"$LOG" 2>&1
import json, sys
print(json.dumps({"content": "📮 쇼츠 루틴 " + __import__('datetime').date.today().isoformat() + "\n" + sys.argv[1],
                  "allowed_mentions": {"parse": []}}))
PY
