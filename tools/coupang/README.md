# 쿠팡파트너스 쇼츠 자동화 파이프라인

```
[상품 입력]             [대본]                [제작]                   [검수 게이트]          [게시]
products.csv  ──┐
(최종승인 전,    ├─▶ script_gen.py ─▶ render.py ──────────▶ run.py check ─▶ 승인 1클릭 ─▶ Metricool 예약
 사람이 링크 생성) │   Claude가 편마다       세로 영상 mp4 (1080x1920)  · 대가성 문구 확인     (approve)     YouTube·인스타
coupang_api.py ─┘   다른 각도로 작성      인스타 캐러셀 8장          · 7일 내 중복 상품 확인               ·틱톡·쓰레드
(최종승인 후 API)   (키 없으면 템플릿)     캡션·해시태그·고정댓글     · 사람 한 줄 입력 확인
```

## 사람이 하는 일 (하루 5분)

1. **최종승인 전:** 주 1회 상품 14개를 골라 파트너스 웹에서 링크를 만들고, `products.csv`에 붙여넣는다.
2. 매일 `out/<날짜>/review.html`을 열어 영상을 훑어본다.
3. 편마다 `my_take` 한 줄을 적는다. 예: "이건 원룸에선 소음이 좀 있음". 이 한 줄이 유튜브·인스타 '비독창 콘텐츠' 판정을 피하는 핵심이다.
4. `python run.py approve <날짜>`를 실행한다.

## 실행

```bash
cd ~/choko-songe-media/tools/coupang
../.venv/bin/python run.py build --csv products.csv --date 2026-10-21   # 대본·영상·캡션 생성
../.venv/bin/python run.py check 2026-10-21                              # 규정 검사
../.venv/bin/python run.py approve 2026-10-21                            # 승인 → queue.json에 approved=true
../.venv/bin/python run.py pending      # 승인됐고 아직 예약 안 된 항목 (일일 루틴이 사용)
../.venv/bin/python run.py unapproved   # 승인 대기 목록
```

## 일일 루틴과의 연결 (tools/daily-routine.sh, 매일 09:47)

1. 정보 쇼츠 작업이 끝나면 `pending` 항목을 Metricool에 예약하고 `mark`로 기록한다.
   - 예약 대상은 인스타 릴스·쓰레드·틱톡이다.
   - 영상은 저장소 루트에 `cp-<날짜>-<상품ID>.mp4`로 올린다.
2. 그다음 `build`로 내일 분량을 만들고 `check` 결과를 보고한다.
3. 승인은 대장님이 `approve`로 한다.
   - D일 09:47에 만든 D+1 분량은 대장님이 D일 중에 승인한다.
   - D+1일 09:47 루틴이 같은 날 21:00·21:30으로 예약한다.

- 게시는 Claude가 `out/<날짜>/queue.json`에서 `approved=true`인 항목만 Metricool로 예약한다.
  - 대상: 봄날 수첩 21:00, 엄마는 늦깎이 대학생 21:30. 인스타 릴스·쓰레드·틱톡에 올리고 유튜브는 제외한다.
  - 자세한 절차는 `~/.claude/skills/making-coupang-shorts`에 있다.
- 매일 아침 예약 작업으로 build를 돌리고, 승인되면 게시하도록 걸어두면 된다.

## 환경변수

| 변수 | 용도 |
|---|---|
| `ANTHROPIC_API_KEY` | 대본 생성용. 없으면 템플릿 대본으로 대체한다 (품질이 낮으니 테스트용으로만 쓴다) |
| `COUPANG_ACCESS_KEY`, `COUPANG_SECRET_KEY` | 최종승인 후 API 자동 수집용 |

## 주의

- `coupang_api.py`의 엔드포인트 경로와 서명 형식은 공식 문서로 검증하지 않았다. 키를 받으면 파트너스 API 가이드와 대조한 뒤 써야 한다.
- 상품 이미지는 API가 주는 이미지 URL이나 직접 찍은 사진만 쓴다. 다른 사람의 리뷰 사진이나 영상은 쓰지 않는다.
