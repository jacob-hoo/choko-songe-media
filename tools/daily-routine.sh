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
- 브랜드별 하루 4개(대장님 지시 2026-11-01, 3개에서 늘림). Metricool: 초코송이 7435740(08:00 아침 한 줄, 12:00·15:00·18:00 하루 한 장. 15:00은 유튜브 제외, 곡까지 하루 6개 한도라서), 봄날 수첩 7435746(09·13·16·19시), 엄마는 늦깎이 대학생 7435751(10·14·17·20시). 7204756·7435778은 아래 [교차 운영] 게스트 슬롯 말고는 손대지 않는다.
- 음원(대장님 지시 2026-11-01): 우리가 만든 음원만, 분위기에 맞게 쓴다. make_cards.py·coupang/render.py가 주제 글자로 곡을 고른다(쉼·위로 오르골, 살림·일상 로파이, 제도·건강·공부 피아노). 안 맞으면 topics.json에 "mood":"snow-night|rain-cafe|exam-night"을 넣는다. 틱톡 autoAddMusic은 틱톡 음악이 붙으므로 쓰지 않는다. 유튜브 설명 끝에 "배경음악: Suno로 만든 AI 연주곡" 한 줄을 넣는다.
- 먼저 getScheduledPosts로 내일 예약을 보고 빈 슬롯만 채운다(재게시용 유튜브 단독 예약은 슬롯으로 세지 않는다).
- 어제·오늘 게시분에 ERROR가 있으면 그 플랫폼만 20:30·21:30 등 빈 시간에 재예약한다(유튜브는 채널당 하루 6개 이하).
- 작업: tools/topics.json(CRLF; python json indent=2, "\n"→"\r\n", 끝 줄바꿈 없음) 추가 → tools/.venv/bin/python tools/make_cards.py --only <id> → 카드 PNG 직접 열어 검수 → mp4를 저장소 루트에 복사, git commit(끝줄 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')·push → raw.githubusercontent.com 200·크기 일치 확인 → createScheduledPost(videoCoverMilliseconds 0, providers youtube·instagram REEL·tiktok·threads, 응답 시각 확인).
- 출처가 분명한 사실만. 기존 주제와 겹치지 않게.
- 주제 방향(2026-10-21 대장님 지시): 봄날 수첩은 50대 이상 부모님(특히 남성 건강·생활)과 부모님 선물을 고르는 자녀가 볼 정보, 엄마는 늦깎이 대학생은 공부법 + 주방 정리·청소·문구 활용. 건강 주제는 공공기관 출처만, 질병 예방·치료 단정 금지.
- 성과 기준(2026-10-26 분석, 볼트 '벤치마킹 결과'): 인스타 릴스는 조회 100~180에서 멈추고 3초 시청률이 2~35%다. 틱톡은 '나에게 해당하는지 확인'형이 터졌다(국민연금 받는 나이, 가정혈압, 냉장고 정리, 소리 내어 읽기).
  - topics.json 각 항목에 "hook"을 넣는다: 2줄 이하, 줄당 12자 안팎, 보는 사람이 자기에게 대입하는 질문 + 숫자(예: "1965년생,\n연금은 몇 살부터?", "냉장고 정리\n10분이면 끝나요?"). make_cards.py가 첫 1.2초를 이 문장만 크게 보여 주고 목록 항목을 하나씩 띄운다.
  - 봄날 수첩은 4편 중 2~3편을 '돈·혜택·나이 기준'(연금·감면·무료 검진·지원금을 출생연도·나이별로)으로, 1편 이상을 건강 수치 확인(혈압·허리둘레 등)으로. 엄마는 4편 중 1편 이상을 눈에 보이는 정리·청소(전/후가 분명한 것)로.
  - 캡션 마지막 줄은 "부모님(가족)께 이 영상 보내 드리세요"처럼 공유를 부르는 한 줄로 끝낸다(인스타는 팔로워 밖 확산에 공유를 크게 본다).
- 목표는 팔로워 증가(대장님 2026-10-26). 영상 끝 1.5초에 팔로우 띠가 자동으로 붙는다. 그 위에 다음을 지킨다.
  - 시리즈: 봄날은 「몇 년생 시리즈」(출생연도·나이로 갈리는 연금·검진·감면·지원 제도)를 매일 1편, hook에 "몇 년생 시리즈 n" 대신 질문을 쓰고 badge를 "봄날 수첩 · 몇 년생 시리즈 n"으로 둔다. 엄마는 「10분 살림 시리즈 n」(전/후가 보이는 정리·청소)을 매일 1편. 캡션 첫 줄 끝에 "(시리즈 n)", 마지막 줄 앞에 "다음 편은 내일 같은 시간, 팔로우해 두세요"(유튜브 설명은 "구독해 두세요")를 넣는다. 이 규칙은 유튜브·인스타·틱톡·스레드 네 곳 모두에 같이 적용한다(같은 영상·같은 캡션, 유튜브 제목은 hook 질문 + #shorts).
  - 협업 게시(대장님 승인 2026-10-26): 화·금요일 봄날 13시 정보 릴스는 instagramData.collaborators=[{"username":"boxheysoo","deleted":false}], 엄마 14시 정보 릴스는 [{"username":"ljw57183800","deleted":false}]로 예약한다. 두 브랜드 모두 맞는 주제(부모님·살림이 겹치는 것)로 고른다. 초대 수락은 대장님이 인스타 앱에서 한다. 협업 예약이 오류를 내면 collaborators 없이 다시 예약하고 "막힌 것"에 적는다.
  - 터진 주제 다시 만들기: 지난 7일 틱톡 조회 상위 3편(getAnalyticsDataByMetrics TKPO07)의 주제를 다른 각도로 한 편씩 새로 만든다(같은 문장·같은 카드 재게시 금지). 예: 국민연금 받는 나이 → 연기연금·조기연금, 냉장고 정리 → 냉동실 정리.

[쿠팡 상품 쇼츠 — 정보 쇼츠가 끝난 뒤. 절차는 ~/.claude/skills/making-coupang-shorts/SKILL.md]
- 대장님 상시 승인(2026-10-21): 클이사가 검수·승인·예약까지 한다. 순서는 제작 → 검수 → 승인 → 예약.
- 제작: tools/.venv/bin/python tools/coupang/run.py build (내일 분량) → run.py check <내일>.
- 검수(클이사 직접): out/<내일>/queue.json 의 캡션·스레드·고정 댓글을 읽고, mp4 첫·마지막 장면(ffmpeg로 프레임 추출)과 캐러셀 jpg를 직접 열어 본다.
  다음 중 하나라도 걸리면 그 상품은 고친 뒤 다시 build --force, 고칠 수 없으면 승인하지 않고 보고한다:
  products.csv 특징 칸에 없는 효능·스펙, 지어낸 경험, 질병 이름·치료·예방 단정, 대가성 문구 누락, 가격 표기 오류, 화면 글자 잘림, 다른 브랜드 말투.
  my_take 가 비어 있으면 특징 칸 사실만으로 한 줄(맞는 사람 + 확인할 점)을 써 넣는다. 써 보지 않은 체험은 쓰지 않는다.
- 승인: 검수를 통과하면 run.py approve <내일>.
- 예약: run.py pending 의 항목 → mp4·캐러셀 jpg를 저장소 루트에 복사·commit·push·raw 200 확인 → 브랜드마다 플랫폼별로 createScheduledPost(instagram REEL(showReelOnFeed=true, 체험 릴스는 팔로워 요건 미달로 실패해 쓰지 않음)+firstCommentText=pinned_comment, instagram 캐러셀 POST 봄날 11:00/엄마 11:30, 같은 시각 tiktok 사진 캐러셀(같은 jpg 5장, tiktokData commercialContentThirdParty=true, autoAddMusic는 쓰지 않음), threads, tiktok 영상 commercialContentThirdParty=true; 유튜브 제외) → run.py mark <date> <product_id> instagram=<id> carousel=<id> tiktok_photo=<id> threads=<id> tiktok=<id>.
- 상품이 없으면(products.csv 소진) 보고만 한다.

[스레드 질문형 글 — 봄날·엄마 하루 2편, 초코송이 1편, 상품 링크 없음]
- tools/.venv/bin/python tools/threads_daily.py <내일> → tools/threads_out/<내일>.json 의 글을 createScheduledPost(providers threads만, media 없음)로 예약 → 응답 id로 tools/.venv/bin/python tools/threads_daily.py mark <topic_id> <id>.

[쿠팡 기획전 — tools/coupang/promos.csv]
- 마감(ends)이 오늘부터 3일 안이고 아직 올리지 않은 기획전이 있으면, 해당 브랜드 스레드에 질문형 글 1편을 내일 09:30(봄날) 또는 10:30(엄마)에 예약한다. 첫 줄은 대가성 문구, 과장·지어낸 경험 금지, "가격·쿠폰은 페이지에서 확인".
- 예약하면 promos.csv의 해당 줄 angle 칸 끝에 " [게시 YYYY-MM-DD]"를 붙인다.

[정보 캐러셀 — 매일 브랜드당 1편(초코송이 포함), 틱톡 사진 게시물이 영상의 2~3배 조회라 2026-11-01 늘림. 고를 주제가 없으면 건너뛴다]
- tools/.venv/bin/python tools/info_carousel.py next silver (엄마는 mom, 초코송이는 choko) → 출력된 card_N.jpg를 저장소 루트에 ic-<topic_id>-N.jpg로 복사·commit·push·raw 200 확인 → createScheduledPost(providers instagram만, instagramData.type POST, media 순서대로, text=out/carousel/<id>/caption.txt + 해시태그 4개) 봄날 07:30 / 엄마 12:00 / 초코송이 10:00 → tools/.venv/bin/python tools/info_carousel.py mark <topic_id> <id>.
- 같은 jpg로 틱톡 사진 게시물도 같은 시각에 따로 예약한다(providers tiktok만, title은 첫 장 제목 30자 이내, 캡션 마지막 줄 "가족에게 보내 주세요"). 틱톡이 인스타보다 반응이 커서다(2026-10-26).
- 우리 음원 슬라이드 영상(틱톡 사진 게시물에는 우리 음원을 넣을 수 없어 따로 만든다): info_carousel.py next <브랜드>로 다음 주제 하나 더 → info_carousel.py video <topic_id> → slideshow.mp4를 저장소 루트에 sl-<topic_id>.mp4로 복사·commit·push·raw 200 확인 → providers tiktok만 createScheduledPost(videoCoverMilliseconds 0, title 30자 이내, 캡션 마지막 줄 "가족에게 보내 주세요") 봄날 21:00 / 엄마 21:30 / 초코송이 21:00 → info_carousel.py mark <topic_id> <id>.

[초코송이 라운지 곡 공개 — 매일, 대장님 지시: "음원 전체를 순차적으로 공개 업로드", "하루 3곡씩"(2026-10-23)]
- tools/.venv/bin/python tools/lounge/singles.py next --days 7 → 항목마다 초코송이(7435740) 유튜브에만 createScheduledPost 한 건: date+time(KST), media=single_url, youtubeData type "video", title=yt_title, category MUSIC, privacy public, madeForKids false, isAiGeneratedContent true, text=description, tags 초코송이·초코송이라운지·연주곡
  → tools/.venv/bin/python tools/lounge/singles.py mark <track_id> single=<id>. release_queue.json 은 commit·push.
- 곡 쇼츠는 올리지 않는다. 초코송이 유튜브 하루 6개 = 카드 쇼츠 3 + 곡 3(롱폼 공개일은 롱폼 1 + 곡 2).

[주간 성과 분석 — 오늘이 월요일일 때만. 절차는 ~/.claude/skills/optimizing-shorts-performance/SKILL.md]
- 봄날 7435746·엄마 7435751의 지난 7일 getAnalyticsDataByMetrics: 인스타 릴스(IGRE02,03,11,23,12,21,24,28), 인스타 게시물·캐러셀, 스레드(THPO02,03,08,09,10,11), 틱톡(TKPO02,05,07,13,15,16).
- getBestTimeToPostByNetwork(instagram, tiktok) 로 시간대를 다시 본다.
- 쿠팡 상품 게시물(cp-)과 정보 게시물을 나눠 도달·3초 시청률·평균 시청·저장·공유 상위/하위 3개를 뽑고, hooks.md '성과 기록'에 hook_type별 한 줄씩 남긴다.
- 지이사 BGM 지원(읽기만): 씨부엉 mrjacobhoo 7204756의 지난 7일 인스타 릴스(IGRE02,03,11,23,24,28)·틱톡(TKPO02,05,07,13,15)을 조회해, ~/NODE-JUN-Vault/50_공통업무/프로젝트/부업/공용 배경음악.md 의 '## 지이사 결과' 아래에 "YYYY-MM-DD 클이사 수집: 게시물별 3초 시청률·평균 시청"을 한 줄씩 추가한다. 이 작업에서 7204756에 게시·수정·예약을 하지 않는다. 토정비결 7435778은 교차 운영 기간의 성과 기록 말고는 조회하지 않는다.
- 결과와 다음 주 바꿀 것 3가지(상품 순서, 훅 유형, 시간대 중)를 ~/NODE-JUN-Vault/50_공통업무/프로젝트/부업/주간 성과.md 맨 위에 날짜 제목으로 추가한다. 저장소에는 올리지 않는다.
- 쿠팡 실적: tools/.venv/bin/python tools/coupang/report.py fetch --days 7 의 클릭·주문·취소·수수료·상품별 수수료를 '주간 성과.md'에 같이 적고, 상품 순서를 정할 때 Metricool 지표보다 수수료·클릭을 먼저 본다. 종료 코드 2(키 없음)면 tools/coupang/out/report/ 의 가장 최근 *-web.json(클이사가 클로드 PC 크롬의 파트너스 화면에서 읽은 값)을 대신 쓰고, 그 파일이 7일보다 오래됐으면 "막힌 것"에 "쿠팡 실적 화면 확인 필요" 한 마디만 쓴다.
- 바꿀 것 중 규칙 안에서 바로 할 수 있는 것(상품 순서 바꾸기, hooks.md 갱신)은 바로 하고, 슬롯 시간·예산이 드는 것은 보고의 "막힌 것"이 아니라 "쿠팡" 줄 뒤에 "제안: …"으로 붙인다.

[교차 운영 — 대장님 지시 2026-11-01. 규칙·일정은 ~/NODE-JUN-Vault/50_공통업무/프로젝트/부업/교차 운영.md 를 먼저 읽고 그대로 따른다]
- 내일이 클이사 게스트 주(씨부엉 7204756 11/09~15·11/23~29 16:00, 토정 7435778 11/16~22 18:00)이고 노트 8행에 대장님 수량 확인이 적혀 있고 중단 표시가 없으면, 그 계정 슬롯과 겹치지 않는지 getScheduledPosts로 보고 클이사 방식(첫 2초 움직임, 질문 훅, 출처, 공용 Suno 곡)으로 주제 범위 안에서 1편을 만든다. 최종본 정보를 hermes -t a2a -z 로 agent jiisa에 context_id 없이 새 대화방으로 보내 호스트 판정을 받고, "통과"일 때만 그 파일로 인스타 REEL·틱톡·스레드·유튜브에 1회 예약한다. 회신이 없거나 수정 필요·위험이면 게시하지 않고 "막힌 것"에 쓴다. 호스트 예약 표에 봄날·엄마·초코 해당 주 예약도 적어 준다. 쿠팡 링크 금지, 상대 게시물·예약·프로필은 건드리지 않는다.
- 오늘이 지이사 게스트 주(봄날 11/09~15 15:00, 엄마 11/16~22 16:00, 초코 11/23~29 16:30, 초코는 유튜브 제외)이면 노트의 "지이사 최종본" 항목을 본다. 오늘 날짜의 최종본이 있으면 호스트로서 SHA-256·출처·금지 표현·소재 중복·첫 장면을 직접 확인해 통과일 때 오늘 슬롯에 1회 예약한다(지이사가 제출을 맡지 않아 클이사가 대리 제출). 없거나 통과 못 하면 게시하지 않고 "막힌 것"에 쓴다.
- 예약 뒤 노트 기록표에 한 줄 적고, tools/coupang/out/metrics/cross.json 배열에 {"date","host":"ssi|tojung|silver|mom|choko","guest","caption":캡션 첫 줄}을 추가한다. 지이사 기록표의 게스트 게시도 같은 파일에 옮긴다.
- 교차 기간에는 호스트 계정(7204756은 ssi, 7435778은 tojung)도 아래 성과 기록에 같은 형식으로 저장한다. track.py의 "교차" 줄이 결과다. 즉시 멈춤 조건이 나오면 그 슬롯을 멈추고 "막힌 것"에 쓴다.
- 월요일이면 주간 성과.md에 교차 잠정 판정(게스트 대 호스트, 계정 순증, 유지·조정·중단 제안)을 쓰고 "쿠팡" 줄 뒤에 "제안: …"으로 한 줄 보고한다. 묶음 비교이므로 단일 원인으로 단정하지 않는다.

[성과 기록 — 매일, 지이사 방식 도입 2026-11-01]
- (2026-11-01부터 게시량 증가: 봄날·엄마 인스타 7·틱톡 8·스레드 7·유튜브 4, 초코송이 인스타 5·틱톡 6·스레드 5·유튜브 6. 편당 조회·도달이 지난주의 절반 아래로 2주 이어지면 "쿠팡" 줄 뒤에 "제안: 편수 조정"으로 보고한다. 틱톡 사진은 자동 음악 없이 나가므로 음원 슬라이드 영상과 조회를 비교한다.)
- 봄날 7435746(키 silver)·엄마 7435751(mom)·초코송이 7435740(choko)의 최근 8일 인스타 릴스(IGRE02,03,23,24,28 순서)와 틱톡(TKPO02,05,07 순서), 팔로워(IGEV01,TKEV07,THEV01,YTEV01)를 getAnalyticsDataByMetrics로 조회해 응답 rows를 그대로 tools/coupang/out/metrics/<오늘>.json 에 {"silver":{"ig":[...],"tk":[...],"ev":[...]},...} 로 저장한다(커밋 안 함). null을 0으로 바꾸지 않는다. 같은 게시물을 날짜별 파일로 비교하면 게시 후 1일·3일·7일 값이 나온다.
- tools/.venv/bin/python tools/track.py 의 출력을 ~/NODE-JUN-Vault/50_공통업무/프로젝트/부업/추적 현황.md 맨 아래에 그대로 붙인다. "경고:"가 "없음"이 아니면 그 내용을 "막힌 것"에 쓴다. 게시 실패(ERROR)는 위 재예약 규칙대로 바로 처리한다.
- 첫 장면 시험: 초코송이는 11/02부터 움직이는 첫 장면, 봄날·엄마는 질문 장면을 유지한다(make_cards.py의 MOTION_BRANDS). 11/08 판정 전에는 이 값을 바꾸지 않는다.
- 첫 장면 시험 판정: 오늘이 2026-11-08 이후이고 ~/NODE-JUN-Vault/20_업무/미처리 업무.md 의 '정보 쇼츠 첫 장면' 항목이 아직 열려 있으면, 11/02~07 초코송이(움직임)와 봄날·엄마(질문), 각 브랜드 쿠팡 릴스의 3초 시청률·평균 시청을 track.py 값으로 비교해(11/03부터 음원 선택 방식과 편수도 함께 바뀌었음을 근거에 밝힌다) "쿠팡" 줄 뒤에 "제안: 첫 장면 유지/되돌리기 + 근거"로 보고한다. 코드는 바꾸지 않는다(대장님 결정 사항).

[쿠팡 실적 — 매일] tools/.venv/bin/python tools/coupang/report.py fetch --days 1 을 돌려 어제 클릭·주문·수수료를 "쿠팡" 줄 끝에 "(어제 클릭 n·주문 n·수수료 n원)"으로 붙인다. 키가 없으면(종료 코드 2) 건너뛴다.

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
