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
- 주제 방향(2026-10-21 대장님 지시): 봄날 수첩은 50대 이상 부모님(특히 남성 건강·생활)과 부모님 선물을 고르는 자녀가 볼 정보, 엄마는 늦깎이 대학생은 공부법 + 주방 정리·청소·문구 활용. 건강 주제는 공공기관 출처만, 질병 예방·치료 단정 금지.

[쿠팡 상품 쇼츠 — 정보 쇼츠가 끝난 뒤. 절차는 ~/.claude/skills/making-coupang-shorts/SKILL.md]
- 대장님 상시 승인(2026-10-21): 클이사가 검수·승인·예약까지 한다. 순서는 제작 → 검수 → 승인 → 예약.
- 제작: tools/.venv/bin/python tools/coupang/run.py build (내일 분량) → run.py check <내일>.
- 검수(클이사 직접): out/<내일>/queue.json 의 캡션·스레드·고정 댓글을 읽고, mp4 첫·마지막 장면(ffmpeg로 프레임 추출)과 캐러셀 jpg를 직접 열어 본다.
  다음 중 하나라도 걸리면 그 상품은 고친 뒤 다시 build --force, 고칠 수 없으면 승인하지 않고 보고한다:
  products.csv 특징 칸에 없는 효능·스펙, 지어낸 경험, 질병 이름·치료·예방 단정, 대가성 문구 누락, 가격 표기 오류, 화면 글자 잘림, 다른 브랜드 말투.
  my_take 가 비어 있으면 특징 칸 사실만으로 한 줄(맞는 사람 + 확인할 점)을 써 넣는다. 써 보지 않은 체험은 쓰지 않는다.
- 승인: 검수를 통과하면 run.py approve <내일>.
- 예약: run.py pending 의 항목 → mp4·캐러셀 jpg를 저장소 루트에 복사·commit·push·raw 200 확인 → 브랜드마다 플랫폼별로 createScheduledPost(instagram REEL(showReelOnFeed=true, 체험 릴스는 팔로워 요건 미달로 실패해 쓰지 않음)+firstCommentText=pinned_comment, instagram 캐러셀 POST 봄날 11:00/엄마 11:30, 같은 시각 tiktok 사진 캐러셀(같은 jpg 5장, tiktokData autoAddMusic=true·commercialContentThirdParty=true), threads, tiktok 영상 commercialContentThirdParty=true(autoAddMusic는 영상에 쓰면 400 오류); 유튜브 제외) → run.py mark <date> <product_id> instagram=<id> carousel=<id> tiktok_photo=<id> threads=<id> tiktok=<id>.
- 상품이 없으면(products.csv 소진) 보고만 한다.

[스레드 질문형 글 — 브랜드당 하루 1편, 상품 링크 없음]
- tools/.venv/bin/python tools/threads_daily.py <내일> → tools/threads_out/<내일>.json 의 글을 createScheduledPost(providers threads만, media 없음)로 예약 → 응답 id로 tools/.venv/bin/python tools/threads_daily.py mark <topic_id> <id>.

[쿠팡 기획전 — tools/coupang/promos.csv]
- 마감(ends)이 오늘부터 3일 안이고 아직 올리지 않은 기획전이 있으면, 해당 브랜드 스레드에 질문형 글 1편을 내일 09:30(봄날) 또는 10:30(엄마)에 예약한다. 첫 줄은 대가성 문구, 과장·지어낸 경험 금지, "가격·쿠폰은 페이지에서 확인".
- 예약하면 promos.csv의 해당 줄 angle 칸 끝에 " [게시 YYYY-MM-DD]"를 붙인다.

[정보 캐러셀 — 내일이 월요일 또는 목요일일 때만, 브랜드당 1편]
- tools/.venv/bin/python tools/info_carousel.py next silver (엄마는 mom) → 출력된 card_N.jpg를 저장소 루트에 ic-<topic_id>-N.jpg로 복사·commit·push·raw 200 확인 → createScheduledPost(providers instagram만, instagramData.type POST, media 순서대로, text=out/carousel/<id>/caption.txt + 해시태그 4개) 봄날 07:30 / 엄마 12:00 → tools/.venv/bin/python tools/info_carousel.py mark <topic_id> <id>.

[초코송이 라운지 곡 공개 — 매일, 대장님 지시: "음원 전체를 순차적으로 공개 업로드", "하루 3곡씩"(2026-10-23)]
- tools/.venv/bin/python tools/lounge/singles.py next --days 7 → 항목마다 초코송이(7435740) 유튜브에만 createScheduledPost 한 건: date+time(KST), media=single_url, youtubeData type "video", title=yt_title, category MUSIC, privacy public, madeForKids false, isAiGeneratedContent true, text=description, tags 초코송이·초코송이라운지·연주곡
  → tools/.venv/bin/python tools/lounge/singles.py mark <track_id> single=<id>. release_queue.json 은 commit·push.
- 곡 쇼츠는 올리지 않는다. 초코송이 유튜브 하루 6개 = 카드 쇼츠 3 + 곡 3(롱폼 공개일은 롱폼 1 + 곡 2).

[주간 성과 분석 — 오늘이 월요일일 때만. 절차는 ~/.claude/skills/optimizing-shorts-performance/SKILL.md]
- 봄날 7435746·엄마 7435751의 지난 7일 getAnalyticsDataByMetrics: 인스타 릴스(IGRE02,03,11,23,12,21,24,28), 인스타 게시물·캐러셀, 스레드(THPO02,03,08,09,10,11), 틱톡(TKPO02,05,07,13,15,16).
- getBestTimeToPostByNetwork(instagram, tiktok) 로 시간대를 다시 본다.
- 쿠팡 상품 게시물(cp-)과 정보 게시물을 나눠 도달·3초 시청률·평균 시청·저장·공유 상위/하위 3개를 뽑고, hooks.md '성과 기록'에 hook_type별 한 줄씩 남긴다.
- 지이사 BGM 지원(읽기만): 씨부엉 mrjacobhoo 7204756의 지난 7일 인스타 릴스(IGRE02,03,11,23,24,28)·틱톡(TKPO02,05,07,13,15)을 조회해, ~/NODE-JUN-Vault/50_공통업무/프로젝트/부업/공용 배경음악.md 의 '## 지이사 결과' 아래에 "YYYY-MM-DD 클이사 수집: 게시물별 3초 시청률·평균 시청"을 한 줄씩 추가한다. 7204756에는 게시·수정·예약을 절대 하지 않는다. 토정비결 7435778은 조회도 하지 않는다.
- 결과와 다음 주 바꿀 것 3가지(상품 순서, 훅 유형, 시간대 중)를 ~/NODE-JUN-Vault/50_공통업무/프로젝트/부업/주간 성과.md 맨 위에 날짜 제목으로 추가한다. 저장소에는 올리지 않는다.
- 바꿀 것 중 규칙 안에서 바로 할 수 있는 것(상품 순서 바꾸기, hooks.md 갱신)은 바로 하고, 슬롯 시간·예산이 드는 것은 보고의 "막힌 것"이 아니라 "쿠팡" 줄 뒤에 "제안: …"으로 붙인다.

- 마지막 출력은 정확히 4줄: "만든 것: …" / "실패·재예약: …" / "쿠팡: 예약 n건, 검수 보류 n건(사유 요약)" / "막힌 것: …(없으면 없음)".
P
)

{
  echo "=== $(date '+%F %T') 시작"
  timeout 3600 "$HOME/.local/bin/claude" -p "$PROMPT" \
    --permission-mode auto \
    --allowedTools "Read,Write,Edit,Glob,Grep,Bash,mcp__claude_ai_Metricool_Social_Media_Management__getScheduledPosts,mcp__claude_ai_Metricool_Social_Media_Management__createScheduledPost,mcp__claude_ai_Metricool_Social_Media_Management__getAnalyticsDataByMetrics,mcp__claude_ai_Metricool_Social_Media_Management__getBestTimeToPostByNetwork" \
    --output-format text
  echo "=== $(date '+%F %T') 끝 (exit $?)"
} >"$LOG" 2>&1

SUMMARY=$(grep -E '^(만든 것|실패·재예약|쿠팡|막힌 것):' "$LOG" | tail -4)
[ -n "$SUMMARY" ] || SUMMARY="루틴이 정상 보고를 남기지 못했습니다. 로그: $LOG"

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
TOKEN=$(grep -E '^DISCORD_BOT_TOKEN=' "$HOME/.hermes/.env" | cut -d= -f2- | tr -d '"'"'")
CH=1554055714505236521
python3 - "$SUMMARY" <<'PY' | curl -s -o /dev/null -w '%{http_code}\n' -X POST \
  -H "Authorization: Bot $TOKEN" -H 'Content-Type: application/json' \
  --data-binary @- "https://discord.com/api/v10/channels/$CH/messages" >>"$LOG" 2>&1
import json, sys
print(json.dumps({"content": "📮 쇼츠 루틴 " + __import__('datetime').date.today().isoformat() + "\n" + sys.argv[1],
                  "allowed_mentions": {"parse": []}}))
PY
