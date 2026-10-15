---
name: posting-choko-songe-shorts
description: 초코송이(대장님 개인 채널) 카드 쇼츠를 만들어 Metricool로 유튜브·인스타·틱톡·쓰레드에 예약 게시하는 절차. 「하루 한 장 지혜」(12:00), 「아침 한 줄」(08:00), 다봄 홍보(점성사 초코송이) 제작·업로드·예약·확인 때 쓴다.
---

# 초코송이 쇼츠 제작·예약 게시

## 고정 정보
- 초코송이 = 대장님 개인 계정·개인 사업(노션 회사ID 「개인(대장)」, PRJ-005, BP-017). 회사 AWS·회사 저장소에 올리지 않는다.
- Metricool: 기본 계정은 **제이콥 계정**(2026-10-15 대장님 결정, Starter 결제 예정). 초코송이는 그 계정 안의 브랜드로 옮긴다. 제이콥 계정 브랜드 ID: 초코송이 7435740 · 봄날 수첩 7435746 · 엄마는 늦깎이 대학생 7435751 (Claude 담당) / mrjacobhoo 7204756 (GPT 담당, 손대지 않음). 옛 초코송이 계정(suminsuheepapa, 브랜드 7291187)은 이전이 끝날 때까지만 쓴다. 시간대 Asia/Seoul. 인스타·쓰레드 @choko_songe_family, 틱톡 @suminsuheepapa, 유튜브 UC8YCpStMkRFzcw0EdGnm8ng.
- 작업 폴더: 대장크롬 `Desktop/claude code/choko-cards/` (venv: Pillow 11.3.0, imageio-ffmpeg 0.6.0).
- 공개 미디어 저장소: github.com/jacob-hoo/choko-songe-media. git push 자격증명이 없으니 Chrome에서 `/upload/main` 페이지로 올린다(한 번에 10MB 미만씩).

## 시리즈
| 시리즈 | 시간 | 형식 | 유튜브 카테고리 |
|---|---|---|---|
| 하루 한 장 지혜 | 12:00 | list / vs / one, 해외 연구·기관 출처 한 줄 | EDUCATION |
| 아침 한 줄 | 08:00 | one, 『파페포포 메모리즈』의 마음을 우리 말로 | PEOPLE_BLOGS |
| 다봄 홍보 | 18:00, 주 1~2회 | 점성사 초코송이(모자+수정구슬), `make_dabom.py` | ENTERTAINMENT |

## 절차
1. `topics.json`에 주제 추가(중복 확인). 한 줄 12자 안팎으로 직접 줄바꿈.
2. `.venv\Scripts\python.exe make_cards.py --only <id>` → `out/<id>.png/.mp4` (7초, 자체 음악 `music/calm-cdfg.wav`).
3. 카드 PNG를 직접 열어 검수: 글자 넘침·잘림, 출처, 캐릭터. 넘치면 문구를 줄이고 다시 만든다.
4. 저장소 업로드 → raw 주소가 200(크기 일치)일 때까지 확인.
5. `createScheduledPost`: providers youtube·instagram(REEL)·tiktok·threads, youtube type=short·madeForKids=false·제목 끝 #shorts. 다봄은 tiktok `commercialContentOwnBrand=true`. 카드뉴스(이미지 여러 장)는 유튜브 제외.
6. 응답의 `publicationDate`가 요청한 시각인지 확인. 다르면 대장님께 플래너에서 직접 옮겨 달라고 한다(2026-10-25처럼 유럽 서머타임 전환일에 1시간 어긋난 사례 있음).
7. 게시 시각 뒤 `getScheduledPosts`로 4곳 PUBLISHED·publicUrl 확인 → 노션 PRJ-005에 기록 → 대장님께 실제 값으로 보고.

## 문구 규칙 (mk-copywriting 적용)
- 쓰지 않는다: 「~이 아니라 ~다」식 반전, 느낌표, 짧은 문구의 긴 줄표(—), 「결과? ~」식 자문자답.
- 금지: 유명인 발언 인용, 책 원문·파페/포포 캐릭터, 투자 권유(돈 카드엔 「투자 권유가 아닙니다」), 의학적 단정, 남의 음악.
- 다봄: 「재미와 자기성찰용, 의료·법률·투자 판단 대체 불가」 고지 필수(building-fortune-service). 꺼져 있는 AI 풀이는 홍보하지 않는다.
- 같은 틀 반복 금지(유튜브 반복 콘텐츠 정책): 내용·말풍선·화자(초코/송이)를 번갈아 바꾼다.

## 하지 않는 것
- 계정 로그인·결제·계정 설정 변경은 대장님이 한다.
- 비밀값은 어디에도 적지 않는다.
