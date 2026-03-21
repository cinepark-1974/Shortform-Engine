# 👖 BLUE JEANS SHORTFORM ENGINE v1.0

> 막장 공식 + 1분 클리프행어 + 과금 전환점 설계  
> **22클릭 → 100화 숏폼 드라마 시나리오 완성**

© 2026 BLUE JEANS PICTURES

---

## 개요

Shortform Engine은 **1~2분 × 80~100화** 세로형(9:16) 숏폼 드라마 시나리오를  
기획부터 집필까지 하나의 엔진 안에서 완결하는 양산형 집필 도구입니다.

- 1편(100화) 시나리오를 **3~5일**에 완성
- **매주 1편** 생산 가능한 시스템
- 드라마박스 / 비글루 / 탑릴스 등 글로벌 숏폼 플랫폼 유통 기준 충족
- 기존 글(소설/시나리오/웹툰/실화)을 막장 숏폼으로 자동 변환

---

## 핵심 수치

| 항목 | 값 |
|------|------|
| 에피소드 길이 | 1~2분 (세로 9:16) |
| 총 에피소드 | 80~100화 |
| 에피소드당 글자 수 | 500~800자 |
| 클리프행어 | 매 화 끝 필수 |
| 과금 전환점 | 15~20화 |
| 타겟 관객 | 30~50대 여성 중심, 모바일 |
| 총 클릭 수 | **22회** (컨셉 1 + 아크 1 + 집필 20) |
| AI 모델 | claude-sonnet-4-6 (속도 우선) |

---

## 기능

### TAB 1 — 새 숏폼 만들기

| 단계 | 내용 |
|------|------|
| **STEP 1 컨셉** | 막장 공식 4종 선택 → 주인공/악역/비밀 입력 → 컨셉 자동 생성 |
| **STEP 2 아크** | 100화 시즌 아크 설계 → EP별 1줄 요약 + 클리프행어 유형 + 과금 포인트 |
| **STEP 3 집필** | 블록 20개 × 5화 = 100화 대본 스트리밍 집필 |
| **STEP 4 다운로드** | 전체 TXT + 아크 CSV 저장 |

### TAB 2 — 기존 글 → 숏폼 변환

텍스트를 붙여넣으면:
- 원본 분석 (핵심 갈등 / 활용 가능한 요소 / 숏폼에 안 맞는 이유)
- 막장 공식으로 변환 전략 설계
- 파일럿 EP1 대본 자동 생성
- "이 컨셉으로 100화 만들기" 버튼으로 STEP 1 파이프라인 연결

---

## 막장 공식 4종

| 공식 | 설명 | 과금 포인트 |
|------|------|-------------|
| **재벌 복수** | 가난한 여주 → 재벌가 → 학대 → 비밀 → 역전 | EP 16: 출생의 비밀 |
| **능력 각성** | 무시당하는 주인공 → 숨겨진 능력 → 경천동지 | EP 16: 첫 능력 발현 |
| **귀환 / 재회** | 5년 후 돌아온 사람 + 아이의 정체 | EP 16: 아이 아버지 폭로 |
| **복수극** | 배신당함 → 새 정체 → 하나씩 무너뜨리기 | EP 16: 첫 복수 성공 |

---

## 파일 구조

```
shortform-engine/
├── main.py              ← Streamlit 메인 앱
├── prompt.py            ← 막장 공식 + 클리프행어 + 프롬프트 빌더
├── requirements.txt
└── .streamlit/
    └── config.toml
```

---

## 설치 및 실행

### 로컬 실행

```bash
git clone https://github.com/your-org/shortform-engine.git
cd shortform-engine
pip install -r requirements.txt
streamlit run main.py
```

`.streamlit/secrets.toml` 생성:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

### Streamlit Cloud 배포

1. GitHub 레포 생성 후 파일 4개 업로드
2. [streamlit.io/cloud](https://streamlit.io/cloud) → New app
3. Repository 선택 → Main file: `main.py`
4. Advanced settings → Secrets:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

5. Deploy

---

## 사용 방법

### 새 숏폼 만들기

1. **막장 공식 선택** — 4종 중 택1 또는 커스텀 아이디어 입력
2. **주인공 설정** — 이름/나이/직업 + 처한 상황 (최대한 불쌍하게)
3. **악역 설정** — 이름/나이/직업 + 관객이 분노하는 행동
4. **핵심 비밀** — EP 몇 화에서 드러나는지 포함해서 2~3개
5. **시즌 질문** — 이 드라마의 핵심 질문 1줄
6. **컨셉 생성** 클릭
7. **아크 생성** 클릭 → 100화 테이블 확인
8. **블록 1~20** 순서대로 클릭 → 5화씩 대본 생성
9. **전체 TXT 다운로드**

### 기존 글 변환

1. **TAB 2** 선택
2. 원본 텍스트 붙여넣기 (최대 3,000자)
3. 변환할 막장 공식 선택
4. **숏폼으로 변환** 클릭
5. 분석 결과 + 파일럿 EP1 확인
6. 마음에 들면 **이 컨셉으로 100화 만들기** 클릭

---

## 기술 스택

| 항목 | 값 |
|------|------|
| Frontend | Streamlit |
| AI | Anthropic Claude (claude-sonnet-4-6) |
| Python | 3.9+ |
| 주요 라이브러리 | anthropic, streamlit, python-docx |

---

## BLUE JEANS PICTURES 엔진 생태계

```
Creator Engine (기획개발) → Writer Engine (영화)
                          → Series Engine (시리즈)
                          → Novel Engine (소설)

Shortform Engine (숏폼) ← 자체 내장 (기획+집필 통합)

Rewrite Engine → 모든 엔진 결과물 고도화
```

Shortform Engine은 **독립 엔진**입니다.  
Creator Engine을 거치지 않고 공식 선택 → 즉시 생산합니다.

---

## 유통 플랫폼

| 플랫폼 | 과금 모델 |
|--------|----------|
| 드라마박스 | 회당 과금 |
| 비글루 | 회당 과금 |
| 탑릴스 | 회당 과금 |
| 숏차 | 회당 과금 |
| 드라마웨이브 | 회당 과금 |
| TikTok | 광고 수익 |
| YouTube Shorts | 광고 수익 |

---

*© 2026 BLUE JEANS PICTURES · Shortform Engine v1.0*
