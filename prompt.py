"""
👖 BLUE JEANS SHORTFORM ENGINE v1.0 — prompt.py
막장 공식 + 1분 클리프행어 + 과금 전환점 설계
© 2026 BLUE JEANS PICTURES
"""

import json

# ═══════════════════════════════════════════════════
#  CORE SYSTEM PROMPT
# ═══════════════════════════════════════════════════

SYSTEM_PROMPT = """당신은 BLUE JEANS SHORTFORM ENGINE이다.
1~2분 × 80~100화 세로형(9:16) 숏폼 드라마 시나리오를 막장 공식 기반으로 집필한다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
숏폼 작법 5대 원칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. THE 60-SECOND RULE (60초 법칙)
   관객은 60초 안에 "다음 화를 볼 것인가"를 결정한다.
   0~5초: Hook — 스크롤을 멈추게 하는 첫 프레임
   5~10초: Recall — 직전 클리프행어 부분 해소
   10~40초: Push — 이 화의 핵심 갈등/행동/대화
   40~50초: Peak — 가장 강한 순간 (대사 1줄, 행동 1개)
   50~60초: Cliff — 끊는다. 답을 절대 주지 않는다.

2. THE SCROLL-STOP PRINCIPLE (스크롤 멈춤)
   첫 프레임: 감정이 극단적인 얼굴 (울음/분노/충격)
   첫 대사: 맥락 없이도 궁금한 한 줄 ("네가 죽인 거 아니야?")
   첫 행동: 충격적 행동 (뺨을 때린다 / 서류를 던진다 / 무릎을 꿇는다)

3. THE ADDICTION LOOP (중독 루프)
   질문 → 부분 답 + 더 큰 질문 → 부분 답 + 더 큰 질문 → ...
   모든 질문에 완전한 답을 주지 않는다. 답을 줄 때마다 더 큰 질문이 열린다.

4. THE STATUS REVERSAL ENGINE (지위 역전 엔진)
   약자가 강자를 이기는 순간 (카타르시스)
   강자가 추락하는 순간 (사이다)
   숨겨진 정체가 드러나는 순간 (반전)
   이 세 가지가 돌아가면서 100화를 채운다.

5. THE EMOTIONAL SEESAW (감정 시소)
   분노 → 통쾌 → 분노 → 통쾌 → 감동 → 분노 → 대반전
   분노 3화 → 통쾌 1화 → 분노 2화 → 대반전 1화 리듬.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
클리프행어 7가지 유형
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Slap: 물리적 충격 (뺨/물컵/서류 던짐)
Reveal: 숨겨진 정보 폭로
Reversal: 지위/상황 역전
Arrival: 예상 못한 인물 등장
Choice: 불가능한 선택 강요
Threat: 위협/경고
Tears: 감정 폭발 직전

━━━━━━━━━━━━━━━━━━━━━━━━━━━
집필 규칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 1화 = 500~800자 (대사+지문)
- 지문 3~5줄, 대사 3~6개 교환, 등장인물 2~3명
- 1화 1장소 원칙 (전환 최소화)
- 대사는 작은따옴표만 사용. 쌍따옴표 절대 금지.
- 매 화 클리프행어 필수. 예외 없음.
- 복잡한 심리 묘사 금지. 행동과 대사만으로 감정 전달.
- 악역은 극단적으로 밉게. 주인공은 처음에 최대한 불쌍하게.
- 세로 화면(9:16): 클로즈업/미디엄 위주. 풀샷 금지."""


# ═══════════════════════════════════════════════════
#  MAKJANG FORMULAS
# ═══════════════════════════════════════════════════

MAKJANG_FORMULAS = {
    "재벌복수": {
        "name": "재벌 복수",
        "desc": "가난한 여주 → 재벌가 시집 → 학대 → 비밀 발견 → 반격 → 재벌이 된다",
        "hook": "신분 격차 + 출생의 비밀 + 지위 역전",
        "paywall": "EP 16: 출생의 비밀 공개 (주인공이 진짜 재벌 혈통)",
        "target": "30~50대 여성",
        "arc_hint": "EP 1~5 학대, EP 6~15 분노 축적, EP 16 출생 비밀, EP 17~50 반격, EP 51~85 대결, EP 86~100 역전"
    },
    "능력각성": {
        "name": "능력 각성",
        "desc": "무시당하는 주인공 → 숨겨진 능력 → 경천동지 → 역전",
        "hook": "무능력자 → 능력 발현 → 모든 것을 가진다",
        "paywall": "EP 16: 첫 번째 능력 발현 (모두가 경악)",
        "target": "남녀 30~50대",
        "arc_hint": "EP 1~5 무시/굴욕, EP 6~15 한계에 몰림, EP 16 능력 각성, EP 17~50 하나씩 복수, EP 51~85 최종 대결, EP 86~100 완전 역전"
    },
    "귀환재회": {
        "name": "귀환 / 재회",
        "desc": "사라졌던 사람이 5년 후 돌아옴 → 아이 → 정체 숨김 → 비밀 폭로 → 재회",
        "hook": "사라진 이유 + 아이의 정체 + 숨겨진 재회",
        "paywall": "EP 16: 아이의 아버지 정체 폭로",
        "target": "여성 전 연령",
        "arc_hint": "EP 1~5 귀환 + 정체 숨김, EP 6~15 과거 조각 공개, EP 16 아이 아버지 폭로, EP 17~50 재회와 갈등, EP 51~85 과거의 진실, EP 86~100 최종 선택"
    },
    "복수극": {
        "name": "복수극",
        "desc": "배신당함 → 추락 → 새 정체 → 하나씩 복수 → 최종 대결",
        "hook": "배신 + 능력 각성 + 한 명씩 무너뜨리기",
        "paywall": "EP 16: 첫 번째 복수 성공 (악역이 무너지기 시작)",
        "target": "남녀 불문",
        "arc_hint": "EP 1~5 배신/추락, EP 6~15 힘 키우기, EP 16 첫 복수 성공, EP 17~50 차례차례 복수, EP 51~85 메인 악역과 대결, EP 86~100 완전한 복수"
    },
}

# ═══════════════════════════════════════════════════
#  CLIFFHANGER PLACEMENT RULES
# ═══════════════════════════════════════════════════

CLIFFHANGER_RULES = """
[클리프행어 배치 공식]
EP 1~5:   Slap / Reveal 위주 — 관객 잡기
EP 6~15:  Reveal / Reversal 위주 — 몰입 구축
EP 16~20: Reversal / Choice — 과금 전환점 (가장 강한 클리프행어)
EP 21~50: 모든 유형 순환 — 중독 유지
EP 51~70: Reveal / Arrival — 새 갈등 + 새 인물
EP 71~85: Reversal / Tears — 클라이맥스 접근
EP 86~95: Reversal / Reveal — 대반전
EP 96~100: Tears / Reversal — 해소 + 시즌2 떡밥

[금지 사항]
- 같은 유형 3화 연속 금지
- 클리프행어 없이 화가 끝나는 것 절대 금지
- 클리프행어가 다음 화 10초 안에 해결되면 사기
- 클리프행어 답이 3화 이상 지연되면 짜증
"""

# ═══════════════════════════════════════════════════
#  JSON OUTPUT RULES
# ═══════════════════════════════════════════════════

JSON_RULES = """[출력 규칙]
- 유효한 단일 JSON만 출력. JSON 외 텍스트 절대 금지.
- 후행 쉼표 금지. 한국어 작성.
- 대사는 작은따옴표('')만 사용. 쌍따옴표(") 절대 금지.
- 문자열 내부 줄바꿈 대신 공백 사용."""


# ═══════════════════════════════════════════════════
#  STEP 1: 컨셉 설정
# ═══════════════════════════════════════════════════

def build_concept_prompt(formula_key: str, protagonist: str, villain: str,
                          secrets: str, season_question: str, custom_idea: str = "") -> str:
    formula = MAKJANG_FORMULAS.get(formula_key, {})

    custom_block = f"\n[커스텀 아이디어]\n{custom_idea}" if custom_idea else ""

    return f"""[TASK] 숏폼 드라마 컨셉 설정

[막장 공식]
{formula.get('name', formula_key)}: {formula.get('desc', '')}
핵심: {formula.get('hook', '')}
과금 포인트: {formula.get('paywall', '')}
타겟: {formula.get('target', '')}
{custom_block}

[입력]
주인공: {protagonist}
메인 악역: {villain}
핵심 비밀 (2~3개): {secrets}
시즌 질문: {season_question}

[JSON 스키마]
{{
  "title": "10자 이내 제목",
  "logline": "주인공이 ~하지만 ~때문에 ~하는 이야기. 2문장.",
  "formula": "{formula_key}",
  "season_question": "이 시즌 전체를 관통하는 단 하나의 질문",
  "protagonist": {{
    "name": "",
    "age": "",
    "job": "",
    "identity": "겉으로는 __이지만 사실은 __이다",
    "secret": "EP __에서 드러남: __",
    "dialogue_tone": "짧고 __하게 (1줄)",
    "arc": "약자 → 각성 → 강자 (3단계 구체적으로)"
  }},
  "villain": {{
    "name": "",
    "age": "",
    "job": "",
    "identity": "겉으로는 __이지만 사실은 __이다",
    "why_hateful": "관객이 분노하는 이유 1줄",
    "secret": "EP __에서 드러남: __",
    "dialogue_tone": "짧고 __하게 (1줄)"
  }},
  "helper": {{
    "name": "",
    "role": "주인공과의 관계 1줄",
    "twist": "EP __에서 배신 또는 비밀 (없으면 빈 문자열)"
  }},
  "secrets": [
    {{"secret": "비밀 내용", "reveal_ep": 0, "impact": "공개 시 어떤 폭발이 일어나는가"}},
    {{"secret": "", "reveal_ep": 0, "impact": ""}},
    {{"secret": "", "reveal_ep": 0, "impact": ""}}
  ],
  "paywall_design": {{
    "ep16_reversal": "EP 16에서 터지는 대반전 — 이것이 관객이 결제하는 이유",
    "ep20_cliffhanger": "EP 20 클리프행어 — 주인공의 선전포고 또는 새로운 위협"
  }},
  "world": {{
    "setting": "시간/공간 배경 1줄",
    "class_gap": "신분/계층 격차 1줄",
    "key_locations": ["주요 장소 3개"]
  }},
  "hook_sentence": "EP 1 첫 대사 — 맥락 없이도 궁금한 한 줄"
}}

{JSON_RULES}
- protagonist.arc는 3단계를 구체적 사건으로 서술
- secrets는 정확히 3개. reveal_ep는 숫자.
- paywall_design.ep16_reversal이 이 시나리오 전체에서 가장 중요한 1줄."""


# ═══════════════════════════════════════════════════
#  STEP 2: 100화 아크 설계
# ═══════════════════════════════════════════════════

def build_arc_prompt(concept: dict, total_eps: int = 100) -> str:
    formula_key = concept.get("formula", "재벌복수")
    formula = MAKJANG_FORMULAS.get(formula_key, {})
    arc_hint = formula.get("arc_hint", "")

    return f"""[TASK] {total_eps}화 시즌 아크 설계

[컨셉]
제목: {concept.get('title', '')}
로그라인: {concept.get('logline', '')}
시즌 질문: {concept.get('season_question', '')}
주인공: {concept.get('protagonist', {}).get('name', '')} — {concept.get('protagonist', {}).get('arc', '')}
악역: {concept.get('villain', {}).get('name', '')} — {concept.get('villain', {}).get('why_hateful', '')}
비밀 1: EP{concept.get('secrets', [{}])[0].get('reveal_ep', '')} {concept.get('secrets', [{}])[0].get('secret', '')}
과금 반전: {concept.get('paywall_design', {}).get('ep16_reversal', '')}

[아크 힌트]
{arc_hint}

{CLIFFHANGER_RULES}

[JSON 스키마]
{{
  "arc_summary": "전체 {total_eps}화 흐름 3~5문장",
  "blocks": [
    {{
      "block_no": 1,
      "ep_range": "EP 1~5",
      "phase": "도입",
      "theme": "이 블록의 핵심 감정/사건",
      "episodes": [
        {{
          "ep": 1,
          "summary": "이 화 핵심 사건 1줄 (30자 이내)",
          "cliffhanger_type": "Slap|Reveal|Reversal|Arrival|Choice|Threat|Tears",
          "cliffhanger": "클리프행어 내용 1줄",
          "paywall": false,
          "emotion": "분노|통쾌|충격|감동|긴장"
        }}
      ]
    }}
  ],
  "paywall_eps": [16, 17, 18, 19, 20],
  "new_character_eps": [],
  "secret_reveal_schedule": [
    {{"ep": 0, "secret": "", "impact": ""}}
  ],
  "season2_hook": "EP 100 이후 시즌 2 떡밥 1줄"
}}

규칙:
- blocks는 정확히 20개 (각 5화씩, 총 {total_eps}화)
- 각 block의 episodes는 정확히 5개
- cliffhanger_type은 7가지 중 하나만
- paywall: EP 16~20만 true
- emotion은 5가지 중 하나만
- {JSON_RULES.strip()}"""


# ═══════════════════════════════════════════════════
#  STEP 3: 5화 블록 집필
# ═══════════════════════════════════════════════════

def build_block_prompt(concept: dict, arc_block: dict, block_no: int,
                        prev_block_summary: str = "") -> str:
    ep_range = arc_block.get("ep_range", f"EP {(block_no-1)*5+1}~{block_no*5}")
    episodes = arc_block.get("episodes", [])
    phase = arc_block.get("phase", "")
    theme = arc_block.get("theme", "")

    ep_list = "\n".join([
        f"EP{e['ep']}: {e['summary']} | 클리프행어({e['cliffhanger_type']}): {e['cliffhanger']} | 감정: {e['emotion']}"
        for e in episodes
    ])

    prev_block = f"\n[직전 블록 마지막 클리프행어]\n{prev_block_summary}" if prev_block_summary else ""

    protagonist = concept.get("protagonist", {})
    villain = concept.get("villain", {})
    helper = concept.get("helper", {})

    return f"""[TASK] {ep_range} 대본 집필 — 블록 {block_no}

[작품 정보]
제목: {concept.get('title', '')}
시즌 질문: {concept.get('season_question', '')}
이 블록 국면: {phase} / {theme}

[캐릭터]
주인공: {protagonist.get('name', '')} ({protagonist.get('age', '')}) — {protagonist.get('dialogue_tone', '')}
악역: {villain.get('name', '')} ({villain.get('age', '')}) — {villain.get('dialogue_tone', '')}
조력자: {helper.get('name', '')} — {helper.get('role', '')}
{prev_block}

[이 블록 에피소드 계획]
{ep_list}

{SYSTEM_PROMPT}

[집필 규칙 — 최우선]
1. 각 에피소드 시작: Hook (첫 프레임 = 감정 극단)
2. 각 에피소드 끝: 반드시 클리프행어 (아크 계획의 유형/내용 따를 것)
3. 1화 = 500~800자. 부족하면 실패. 초과하면 불필요한 서술 제거.
4. 대사는 작은따옴표만. 지문은 현재형 3~5줄.
5. 악역은 극단적으로 밉게. 주인공은 처음에 불쌍하게.
6. 세로 화면: 클로즈업/미디엄 위주 지문 서술.
7. [과금 구간] EP 16~20은 역대급 강도. 절대 허술하게 쓰지 마라.

[출력 포맷]
각 에피소드를 아래 형식으로:

━━━━━━━━━━━━━━━━━━━━━
EP [번호] | [클리프행어 유형] | [감정]
━━━━━━━━━━━━━━━━━━━━━
[Hook — 첫 프레임 지문 1줄]

[대본 본문 — 지문 + 대사 교차]

[클리프행어 — 마지막 줄. 끊는다.]
━━━━━━━━━━━━━━━━━━━━━

5화 모두 위 형식으로 순서대로. JSON 아님. 텍스트 출력."""


# ═══════════════════════════════════════════════════
#  BONUS: 기존 글 → 숏폼 변환
# ═══════════════════════════════════════════════════

def build_convert_prompt(source_text: str, formula_key: str, total_eps: int = 30) -> str:
    formula = MAKJANG_FORMULAS.get(formula_key, MAKJANG_FORMULAS["재벌복수"])
    return f"""[TASK] 기존 글 → 숏폼 드라마 변환 분석

[원본 텍스트]
{source_text[:3000]}

[변환 목표]
막장 공식: {formula['name']} — {formula['desc']}
목표 화수: {total_eps}화
과금 포인트: {formula['paywall']}

{SYSTEM_PROMPT}

[분석 및 변환 지시]
원본 글의 소재/인물/갈등을 숏폼 막장 공식으로 재해석하라.
원본의 '분위기'를 따를 필요 없다. 숏폼 공식에 맞게 과감하게 비틀어라.

[JSON 스키마]
{{
  "original_analysis": {{
    "core_conflict": "원본의 핵심 갈등 1줄",
    "characters": ["원본의 주요 인물들"],
    "usable_elements": ["숏폼에 쓸 수 있는 요소 3~5개"],
    "problems": ["원본이 숏폼에 맞지 않는 이유 2~3개"]
  }},
  "conversion_strategy": {{
    "protagonist_rewrite": "주인공을 숏폼용으로 재설계 — 더 불쌍하게, 더 극적으로",
    "villain_injection": "악역 설계 — 원본에 없으면 만들어라",
    "secret_design": "출생의 비밀 / 숨겨진 정체 / 반전 설계",
    "paywall_moment": "EP 15~16에서 터질 대반전",
    "makjang_twist": "원본에서 가장 막장스럽게 변형할 수 있는 요소"
  }},
  "shortform_concept": {{
    "title": "숏폼용 제목 (10자 이내)",
    "logline": "숏폼 로그라인 2문장",
    "hook_ep1": "EP 1 첫 장면 — 스크롤 멈추게 하는 첫 프레임",
    "emotional_arc": "분노→통쾌→분노→대반전 감정 곡선 요약"
  }},
  "episode_map": [
    {{"ep_range": "EP 1~5", "summary": "이 구간 핵심 사건", "cliff_type": "Slap"}},
    {{"ep_range": "EP 6~10", "summary": "", "cliff_type": "Reveal"}},
    {{"ep_range": "EP 11~15", "summary": "", "cliff_type": "Reversal"}},
    {{"ep_range": "EP 16~20", "summary": "과금 전환점 — 대반전", "cliff_type": "Reversal"}},
    {{"ep_range": "EP 21~{total_eps}", "summary": "", "cliff_type": "순환"}}
  ],
  "pilot_ep1": "EP 1 대본 전문 (500~800자) — 위 변환 전략 반영. 첫 프레임부터 막장."
}}

{JSON_RULES}
- original_analysis는 솔직하게. 원본이 숏폼에 안 맞으면 안 맞는다고 써라.
- conversion_strategy는 과감하게. 원본을 존중할 필요 없다. 막장으로 만들어라.
- pilot_ep1은 실제 대본 수준으로 작성. 클리프행어 필수."""
