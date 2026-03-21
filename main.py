"""
👖 BLUE JEANS SHORTFORM ENGINE v2.1 — main.py
The Ultimate Shortform Drama Engine
© 2026 BLUE JEANS PICTURES
"""

import streamlit as st
import anthropic
import json
import re
from datetime import datetime
import prompt as P

# 모델 분업: 집필(Opus) / 설계(Sonnet)
MODEL_WRITE = "claude-opus-4-6"    # 블록 집필 — 완성도 최우선
MODEL_PLAN  = "claude-sonnet-4-6"  # 컨셉·아크·변환 — 속도·비용 효율
MAX_TOKENS_CONCEPT  = 6000
MAX_TOKENS_ARC      = 16000
MAX_TOKENS_BLOCK    = 12000   # Opus — 토큰 여유 확보
MAX_TOKENS_CONVERT  = 10000

st.set_page_config(
    page_title="BLUE JEANS · Shortform Engine",
    page_icon="👖", layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@latest/Paperlogy.css');
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&display=swap');
:root {
    --navy:#191970;--y:#FFCB05;--bg:#F7F7F5;--card:#FFFFFF;
    --card-border:#E2E2E0;--t:#1A1A2E;--r:#D32F2F;--g:#2EC484;
    --dim:#8E8E99;--light-bg:#EEEEF6;--orange:#FF6B35;--pink:#FF69B4;
    --body:'Pretendard',-apple-system,sans-serif;
    --heading:'Paperlogy','Pretendard',sans-serif;
    --display:'Playfair Display','Paperlogy',serif;
}
html,body,[class*="css"]{font-family:var(--body);color:var(--t);-webkit-font-smoothing:antialiased;}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],
[data-testid="stMainBlockContainer"],[data-testid="stHeader"],[data-testid="stBottom"]{
    background-color:var(--bg)!important;color:var(--t)!important;}
.stMarkdown,.stText{color:var(--t)!important;}
h1,h2,h3,h4,h5,h6{color:var(--navy)!important;font-family:var(--heading)!important;}
section[data-testid="stSidebar"]{display:none;}
.stTextInput input,.stTextArea textarea,
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{
    background-color:var(--card)!important;color:var(--t)!important;
    border:1.5px solid var(--card-border)!important;border-radius:8px!important;
    font-family:var(--body)!important;font-size:0.9rem!important;padding:0.6rem 0.8rem!important;}
.stTextInput input:focus,.stTextArea textarea:focus{
    border-color:var(--navy)!important;box-shadow:0 0 0 2px rgba(25,25,112,0.08)!important;}
.stSelectbox>div>div,[data-baseweb="select"]>div{
    background-color:var(--card)!important;color:var(--t)!important;
    border-color:var(--card-border)!important;border-radius:8px!important;}
[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"],[role="option"]{
    background-color:var(--card)!important;color:var(--t)!important;}
[role="option"]:hover{background-color:var(--light-bg)!important;}
.stTextInput label,.stTextArea label,.stSelectbox label{
    color:var(--t)!important;font-weight:600!important;font-size:0.82rem!important;}
.stButton>button{
    color:var(--t)!important;border:1.5px solid var(--card-border)!important;
    background-color:var(--card)!important;border-radius:8px!important;
    font-family:var(--body)!important;font-weight:600!important;
    font-size:0.85rem!important;padding:0.5rem 1.2rem!important;transition:all 0.2s;}
.stButton>button:hover{border-color:var(--navy)!important;}
.stButton>button[kind="primary"],.stButton>button[data-testid="stBaseButton-primary"]{
    background-color:var(--y)!important;color:var(--navy)!important;
    border-color:var(--y)!important;font-weight:700!important;}
.stButton>button[kind="primary"]:hover{background-color:#E8B800!important;}
[data-testid="stDownloadButton"] button{
    background-color:var(--navy)!important;color:white!important;
    border-color:var(--navy)!important;font-weight:700!important;}
.stExpander details summary{
    background-color:var(--card)!important;color:var(--t)!important;
    border:1px solid var(--card-border)!important;border-radius:8px!important;}
details[open]>div{background-color:var(--card)!important;}
.stCaption,small{color:var(--dim)!important;}
.stAlert{border-radius:8px!important;}
[data-testid="stVerticalBlock"],[data-testid="stHorizontalBlock"],
[data-testid="stColumn"]{background-color:transparent!important;}
hr{border-color:var(--card-border)!important;}

/* 브랜드 */
.header{font-size:0.85rem;font-weight:700;color:var(--navy);letter-spacing:0.15em;font-family:var(--heading);}
.brand-title{font-size:2.6rem;font-weight:900;color:var(--navy);font-family:var(--display);letter-spacing:-0.02em;}
.sub{font-size:0.72rem;font-weight:600;letter-spacing:0.18em;color:var(--dim);}

/* 컴포넌트 */
.card{background:var(--card);border:1px solid var(--card-border);border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1rem;}
.callout{background:var(--light-bg);border-left:4px solid var(--y);border-radius:0 8px 8px 0;padding:0.8rem 1rem;margin-bottom:0.8rem;}
.cl{font-size:0.72rem;font-weight:700;color:var(--navy);letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.3rem;}
.section-header{font-size:1.05rem;font-weight:800;color:var(--navy);font-family:var(--heading);
    padding:0.5rem 0;border-bottom:2px solid var(--y);margin-bottom:1rem;}
.en{font-size:0.7rem;font-weight:600;color:var(--dim);letter-spacing:0.1em;margin-left:0.5rem;}
.ri{background:var(--card);border:1px solid var(--card-border);border-left:3px solid var(--navy);
    border-radius:0 8px 8px 0;padding:0.7rem 1rem;margin-bottom:0.5rem;}
.rl{font-size:0.7rem;font-weight:700;color:var(--dim);margin-bottom:0.2rem;}
.big{font-size:3rem;font-weight:900;color:var(--navy);line-height:1;}

/* 스텝바 */
.step-bar{display:flex;align-items:center;justify-content:center;gap:0;margin:1.5rem 0;}
.step-dot{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:0.8rem;}
.step-dot.done{background:var(--g);color:white;}
.step-dot.active{background:var(--y);color:var(--navy);}
.step-dot.wait{background:#E6E9EF;color:#AAA;}
.step-line{flex:1;height:2px;background:#E6E9EF;max-width:80px;}
.step-line.done{background:var(--g);}

/* EP 대본 */
.ep-block{background:var(--card);border:1px solid var(--card-border);border-left:4px solid var(--orange);
    border-radius:0 12px 12px 0;padding:1.2rem 1.4rem;margin-bottom:1rem;}
.ep-header{font-size:0.9rem;font-weight:800;color:var(--orange);letter-spacing:0.05em;margin-bottom:0.8rem;}

/* 도파민 배지 */
.d-badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:0.68rem;font-weight:800;margin:2px;}
.d1{background:#FFE0B2;color:#E65100;}.d2{background:#E8F5E9;color:#2E7D32;}
.d3{background:#E3F2FD;color:#1565C0;}.d4{background:#F3E5F5;color:#6A1B9A;}
.d5{background:#FCE4EC;color:#880E4F;}.d6{background:#FFF3E0;color:#E65100;}
.d7{background:#EFEBE9;color:#4E342E;}.d8{background:#E0F7FA;color:#006064;}
</style>
""", unsafe_allow_html=True)


# ─── 세션 초기화 ───
def init():
    defaults = {
        "step": 0, "concept": None, "arc": None,
        "blocks": {}, "convert_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init()


# ─── 유틸리티 ───
def get_client():
    k = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not k:
        st.error("ANTHROPIC_API_KEY가 secrets에 없습니다.")
        st.stop()
    return anthropic.Anthropic(api_key=k)

def safe_json(text):
    if not text: return None
    try: return json.loads(text)
    except:
        try: return json.loads(re.sub(r'```json\s*|```\s*', '', text).strip())
        except: return None

def call_claude(prompt, max_tokens, system="", model=None):
    client = get_client()
    kwargs = {"model": model or MODEL_PLAN, "max_tokens": max_tokens,
              "messages": [{"role": "user", "content": prompt}]}
    if system: kwargs["system"] = system
    r = client.messages.create(**kwargs)
    return "".join(b.text for b in r.content if hasattr(b, "text")).strip()

def call_stream(prompt, max_tokens, system="", model=None):
    client = get_client()
    kwargs = {"model": model or MODEL_WRITE, "max_tokens": max_tokens,
              "messages": [{"role": "user", "content": prompt}]}
    if system: kwargs["system"] = system
    with client.messages.stream(**kwargs) as s:
        for t in s.text_stream:
            yield t

def render_step_bar(step):
    labels = ["컨셉", "아크", "집필", "다운로드"]
    dots = ""
    for i, lbl in enumerate(labels):
        cls = "done" if step > i else ("active" if step == i else "wait")
        sym = "✓" if step > i else str(i+1)
        dots += (f'<div style="display:flex;flex-direction:column;align-items:center;gap:5px;">'
                 f'<div class="step-dot {cls}">{sym}</div>'
                 f'<div style="font-size:0.68rem;opacity:0.65">{lbl}</div></div>')
        if i < 3:
            lc = "done" if step > i else ""
            dots += f'<div class="step-line {lc}"></div>'
    st.markdown(f'<div class="step-bar">{dots}</div>', unsafe_allow_html=True)

def dopamine_badge(d_type):
    cls_map = {"D1":"d1","D2":"d2","D3":"d3","D4":"d4","D5":"d5","D6":"d6","D7":"d7","D8":"d8"}
    name_map = {
        "D1":"간헐적강화","D2":"지위역전","D3":"정체드러남","D4":"예측오류",
        "D5":"위험+설렘","D6":"밀당","D7":"대리복수","D8":"체크리스트"
    }
    result = ""
    for d in ["D1","D2","D3","D4","D5","D6","D7","D8"]:
        if d in str(d_type):
            cls = cls_map.get(d, "")
            name = name_map.get(d, d)
            result += f'<span class="d-badge {cls}">{name}</span>'
    return result or f'<span class="d-badge d8">{d_type}</span>'


# ─── 브랜드 헤더 ───
st.markdown(
    '<div style="text-align:center;padding:1rem 0 0 0">'
    '<div class="header">B L U E &nbsp; J E A N S &nbsp; P I C T U R E S</div>'
    '<div class="brand-title">SHORTFORM ENGINE</div>'
    '<div class="sub">v2.0 &nbsp;·&nbsp; DOPAMINE DESIGN &nbsp;·&nbsp; 100EP &nbsp;·&nbsp; PAYWALL</div>'
    '</div>',
    unsafe_allow_html=True
)
st.caption(f"집필: {MODEL_WRITE} · 설계: {MODEL_PLAN} · 22클릭 → 100화 완성 · 도파민 설계 내장")

tab_create, tab_convert = st.tabs(["✍️ 새 숏폼 만들기", "🔄 기존 글 → 숏폼 변환"])


# ═══════════════════════════════════════════════════
#  TAB 1: 새 숏폼 만들기
# ═══════════════════════════════════════════════════
with tab_create:
    render_step_bar(st.session_state.step)
    st.markdown('<hr>', unsafe_allow_html=True)

    # ── STEP 1: 컨셉 ──
    st.markdown('<div class="section-header">STEP 1 &nbsp; 컨셉 설정 <span class="en">CONCEPT SETUP</span></div>', unsafe_allow_html=True)

    formula_options = {
        "재벌복수": "👑 재벌 복수 — 신분 격차 + 출생의 비밀 + 지위 역전",
        "능력각성": "⚡ 능력 각성 — 무시당한 주인공의 숨겨진 능력",
        "귀환재회": "🔄 귀환 / 재회 — 5년 후 돌아온 사람 + 아이의 정체",
        "복수극":   "🗡️ 복수극 — 배신당함 → 하나씩 무너뜨리기",
        "감성숏폼": "💕 감성 숏폼 — 설렘+배신+눈물 (원작 변환형)",
    }

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        formula_key = st.selectbox("막장 공식", list(formula_options.keys()),
                                    format_func=lambda x: formula_options[x], key="fs")
        formula = P.MAKJANG_FORMULAS[formula_key]
        st.markdown(
            f'<div class="callout"><div class="cl">공식 설명</div>{formula["desc"]}<br>'
            f'<span style="font-size:.8rem;color:var(--navy);font-weight:700">💰 과금:</span>'
            f'<span style="font-size:.8rem"> {formula["paywall"]}</span><br>'
            f'<span style="font-size:.75rem;color:var(--orange)">🧠 도파민 키: {formula["dopamine_key"][:60]}...</span>'
            f'</div>', unsafe_allow_html=True
        )

    with col_f2:
        col_m, col_r = st.columns(2)
        with col_m:
            market = st.selectbox("타겟 시장", ["한국", "글로벌", "중국"], key="mkt")
        with col_r:
            rating = st.selectbox("수위 등급",
                ["family", "teen", "adult"],
                format_func=lambda x: {"family":"👨‍👩‍👧 전체가","teen":"🔞 15세 이상","adult":"🔞 성인(19+)"}[x],
                index=1, key="rtg"
            )
        total_eps = st.selectbox("총 에피소드 수", [80, 90, 100], index=2)
        if market in ["중국","글로벌"]:
            st.markdown(
                f'<div class="ri" style="border-left:3px solid #D32F2F">'
                f'<div class="rl" style="color:#D32F2F">🇨🇳 중국 특화</div>'
                f'<div style="font-size:.75rem">{formula.get("china_variant","")[:80]}...</div>'
                f'</div>', unsafe_allow_html=True
            )
        rating_info = P.CONTENT_RATING_RULES[rating]
        st.markdown(
            f'<div class="ri" style="border-left:3px solid var(--orange)">'
            f'<div class="rl" style="color:var(--orange)">🧠 도파민 연출</div>'
            f'<div style="font-size:.75rem">{rating_info["dopamine_note"][:80]}...</div>'
            f'</div>', unsafe_allow_html=True
        )

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        protagonist = st.text_area("주인공 설정",
            placeholder="이름 / 나이 / 직업\n처한 상황 (최대한 불쌍하게 — 낙차가 클수록 역전의 도파민이 크다)\n숨겨진 능력/정체/비밀 (역전의 씨앗)",
            height=100)
        secrets = st.text_area("핵심 비밀 2~3개",
            placeholder="비밀1: EP__에서 드러남 — 내용\n비밀2: EP__에서 드러남 — 내용\n비밀3: EP__에서 드러남 — 내용",
            height=80)
    with col_i2:
        villain = st.text_area("메인 악역 설정",
            placeholder="이름 / 나이 / 직업\n구체적 나쁜 짓 (관객이 '저거 우리 회사에도 있어!'라고 할 수 있는 것)\n숨겨진 비밀 또는 약점",
            height=100)
        season_question = st.text_input("시즌 질문",
            placeholder="이 드라마의 핵심 질문 1줄 — 이것이 100화 동안 답을 안 주는 질문")

    custom_idea = st.text_area("커스텀 아이디어 (선택)",
        placeholder="공식 변형 또는 특별한 설정", height=60)

    if st.button("🧠 컨셉 + 도파민 설계 생성", type="primary", use_container_width=True):
        if not protagonist or not villain or not season_question:
            st.error("주인공 / 악역 / 시즌 질문을 모두 입력하세요.")
        else:
            with st.spinner("컨셉 + 도파민 설계 중... (20~40초)"):
                raw = call_claude(
                    P.build_concept_prompt(formula_key, protagonist, villain,
                                           secrets or "자동 생성", season_question,
                                           custom_idea, market, rating),
                    MAX_TOKENS_CONCEPT
                )
                result = safe_json(raw)
                if result:
                    result["total_eps"] = total_eps
                    st.session_state.concept = result
                    st.session_state.step = 1
                    st.rerun()
                else:
                    st.error("생성 실패. 다시 시도하세요.")
                    with st.expander("Raw"): st.text(raw[:1000])

    # ── 컨셉 결과 ──
    if st.session_state.concept:
        c = st.session_state.concept
        st.markdown("---")
        st.markdown(f'<div class="section-header">📋 {c.get("title","")} — 컨셉 완성</div>', unsafe_allow_html=True)

        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            st.markdown(f'<div class="callout"><div class="cl">로그라인</div>{c.get("logline","")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="callout"><div class="cl">시즌 질문</div>{c.get("season_question","")}</div>', unsafe_allow_html=True)
        with col_c2:
            st.markdown(f'<div class="ri"><div class="rl">🎯 Hook 첫 대사</div>{c.get("hook_sentence","")}</div>', unsafe_allow_html=True)
            if c.get("first_subtitle"):
                st.markdown(f'<div class="ri" style="border-left:3px solid var(--orange)"><div class="rl" style="color:var(--orange)">📱 첫 자막</div>{c["first_subtitle"]}</div>', unsafe_allow_html=True)

        # 도파민 설계
        dd = c.get("dopamine_design", {})
        if dd:
            st.markdown('<div class="section-header">🧠 도파민 설계 <span class="en">DOPAMINE DESIGN</span></div>', unsafe_allow_html=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if dd.get("primary_triggers"):
                    triggers_html = "".join([f'<div style="margin:.3rem 0;font-size:.85rem">• {t}</div>' for t in dd["primary_triggers"]])
                    st.markdown(f'<div class="card" style="border-left:4px solid var(--orange)"><div class="cl">🧠 주력 도파민 트리거</div>{triggers_html}</div>', unsafe_allow_html=True)
                if dd.get("addiction_loop"):
                    st.markdown(f'<div class="ri"><div class="rl">🔄 중독 루프</div>{dd["addiction_loop"]}</div>', unsafe_allow_html=True)
            with col_d2:
                if dd.get("seesaw_pattern"):
                    st.markdown(f'<div class="ri"><div class="rl">⚖️ 감정 시소 패턴</div>{dd["seesaw_pattern"]}</div>', unsafe_allow_html=True)
                if dd.get("reversal_timing"):
                    st.markdown(f'<div class="ri"><div class="rl">💥 역전 타이밍 전략</div>{dd["reversal_timing"]}</div>', unsafe_allow_html=True)
                if dd.get("reveal_schedule"):
                    st.markdown(f'<div class="ri"><div class="rl">🔓 정체 드러남 로드맵</div>{dd["reveal_schedule"]}</div>', unsafe_allow_html=True)

        # 주인공 / 악역
        col_p, col_v = st.columns(2)
        with col_p:
            p = c.get("protagonist", {})
            st.markdown(
                f'<div class="card"><div class="cl">🔥 주인공: {p.get("name","")} ({p.get("age","")})</div>'
                f'<div style="font-size:.8rem;color:var(--r)">시작 상태: {p.get("start_state","")}</div>'
                f'<div style="font-size:.85rem;margin:.3rem 0">{p.get("identity","")}</div>'
                f'<div style="font-size:.8rem;color:var(--navy);font-weight:700">🎭 숨겨진 힘: {p.get("hidden_power","")}</div>'
                f'<div style="font-size:.8rem;color:var(--dim);margin-top:.3rem">비밀: {p.get("secret","")}</div>'
                f'<div style="font-size:.8rem;color:var(--g)">아크: {p.get("arc","")}</div>'
                f'</div>', unsafe_allow_html=True
            )
        with col_v:
            v = c.get("villain", {})
            st.markdown(
                f'<div class="card" style="border-left:4px solid var(--r)">'
                f'<div class="cl">🖤 악역: {v.get("name","")} ({v.get("age","")})</div>'
                f'<div style="font-size:.85rem">{v.get("identity","")}</div>'
                f'<div style="font-size:.8rem;color:var(--r);margin-top:.3rem;font-weight:700">구체적 나쁜 짓: {v.get("specific_evil","")}</div>'
                f'<div style="font-size:.8rem;color:var(--dim)">몰락: {v.get("downfall","")}</div>'
                f'</div>', unsafe_allow_html=True
            )

        # 조력자 / 경쟁자
        col_h, col_ri = st.columns(2)
        with col_h:
            h = c.get("helper", {})
            if h.get("name"):
                st.markdown(
                    f'<div class="ri"><div class="rl">💙 조력자: {h.get("name","")}</div>'
                    f'{h.get("role","")}<br>'
                    f'<span style="font-size:.78rem;color:var(--orange)">⚠️ 숨겨진 의도: {h.get("hidden_agenda","")}</span></div>',
                    unsafe_allow_html=True
                )
        with col_ri:
            ri = c.get("rival", {})
            if ri.get("name"):
                st.markdown(
                    f'<div class="ri"><div class="rl">🥊 경쟁자: {ri.get("name","")}</div>'
                    f'일시적 우위: {ri.get("advantage","")}<br>'
                    f'<span style="font-size:.78rem;color:var(--dim)">역할: {ri.get("purpose","")}</span></div>',
                    unsafe_allow_html=True
                )

        # 과금 설계
        pd = c.get("paywall_design", {})
        ep16_d = pd.get("ep16_dopamine", "")
        ep16_c = pd.get("ep16_china", "")
        china_note = f'<div style="font-size:.78rem;color:#D32F2F;margin-top:.3rem">🇨🇳 {ep16_c}</div>' if ep16_c else ""
        st.markdown(
            f'<div class="card" style="border-left:4px solid var(--y)">'
            f'<div class="cl">💰 과금 전환점 (EP 16~20)</div>'
            f'<div style="font-size:.95rem;font-weight:700">{pd.get("ep16_reversal","")}</div>'
            f'<div style="margin-top:.3rem">{dopamine_badge(ep16_d)}</div>'
            f'{china_note}'
            f'<div style="font-size:.85rem;color:var(--dim);margin-top:.3rem">EP 20: {pd.get("ep20_cliffhanger","")}</div>'
            f'</div>', unsafe_allow_html=True
        )

        # 비밀 스케줄
        secrets_data = c.get("secrets", [])
        if secrets_data:
            s_html = "".join([
                f'<div style="font-size:.85rem;margin:.3rem 0">'
                f'• EP{s.get("reveal_ep","?")} — {s.get("secret","")} → {s.get("impact","")} '
                f'{dopamine_badge(s.get("dopamine_type",""))}</div>'
                for s in secrets_data if s.get("secret")
            ])
            st.markdown(f'<div class="ri"><div class="rl">🔒 비밀 공개 스케줄</div>{s_html}</div>', unsafe_allow_html=True)

        # 장소 설계
        ld = c.get("location_design", {})
        if ld:
            st.markdown('<div class="section-header">📍 장소 설계 <span class="en">LOCATION DESIGN</span></div>', unsafe_allow_html=True)
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                main_locs = ld.get("main_locations", [])
                if main_locs:
                    loc_html = "".join([
                        f'<div style="font-size:.85rem;margin:.3rem 0">'
                        f'<b>{l.get("name","")}</b> — {l.get("emotion_role","")}<br>'
                        f'<span style="font-size:.75rem;color:var(--orange)">도파민 장면: {l.get("dopamine_scene","")}</span></div>'
                        for l in main_locs if l.get("name")
                    ])
                    st.markdown(f'<div class="ri"><div class="rl">🏠 주 장소</div>{loc_html}</div>', unsafe_allow_html=True)
                if ld.get("sub_locations"):
                    st.markdown(f'<div class="ri"><div class="rl">📌 보조 장소</div>{" · ".join(ld["sub_locations"])}</div>', unsafe_allow_html=True)
            with col_l2:
                if ld.get("reversal_location"):
                    st.markdown(f'<div class="ri" style="border-left:3px solid var(--g)"><div class="rl" style="color:var(--g)">💥 역전 장소</div>{ld["reversal_location"]}</div>', unsafe_allow_html=True)
                if ld.get("cliffhanger_location"):
                    st.markdown(f'<div class="ri" style="border-left:3px solid var(--r)"><div class="rl" style="color:var(--r)">⚡ 클리프행어 장소</div>{ld["cliffhanger_location"]}</div>', unsafe_allow_html=True)
                if ld.get("romance_peak"):
                    st.markdown(f'<div class="ri" style="border-left:3px solid var(--pink)"><div class="rl" style="color:var(--pink)">💕 로맨스 피크</div>{ld["romance_peak"]}</div>', unsafe_allow_html=True)

    # ── STEP 2: 아크 ──
    if st.session_state.step >= 1 and st.session_state.concept:
        st.markdown("---")
        st.markdown('<div class="section-header">STEP 2 &nbsp; 100화 아크 설계 <span class="en">SEASON ARC</span></div>', unsafe_allow_html=True)

        if st.button("📊 100화 아크 + 도파민 마일스톤 생성", type="primary", use_container_width=True):
            total = st.session_state.concept.get("total_eps", 100)
            with st.spinner("100화 아크 + 도파민 설계 중... (40~60초)"):
                raw = call_claude(P.build_arc_prompt(st.session_state.concept, total), MAX_TOKENS_ARC)
                result = safe_json(raw)
                if result:
                    st.session_state.arc = result
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.error("아크 생성 실패.")
                    with st.expander("Raw"): st.text(raw[:2000])

        if st.session_state.arc:
            arc = st.session_state.arc
            st.markdown(f'<div class="callout"><div class="cl">아크 요약</div>{arc.get("arc_summary","")}</div>', unsafe_allow_html=True)

            # 도파민 마일스톤
            milestones = arc.get("dopamine_milestones", [])
            if milestones:
                with st.expander(f"🧠 도파민 마일스톤 {len(milestones)}개"):
                    for m in milestones:
                        d_html = dopamine_badge(m.get("type",""))
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #E6E9EF">'
                            f'<div style="min-width:50px;font-weight:700;font-size:.85rem">EP {m.get("ep","")}</div>'
                            f'{d_html}'
                            f'<div style="font-size:.85rem">{m.get("event","")}</div>'
                            f'</div>', unsafe_allow_html=True
                        )

            # 100화 테이블
            blocks = arc.get("blocks", [])
            if blocks:
                table_rows = ""
                for block in blocks:
                    for ep in block.get("episodes", []):
                        ep_no = ep.get("ep", 0)
                        is_paywall = ep_no in arc.get("paywall_eps", [16,17,18,19,20])
                        badge = '<span style="background:var(--y);color:var(--navy);padding:1px 6px;border-radius:10px;font-size:.65rem;font-weight:800">💰</span>' if is_paywall else (
                            '<span style="background:var(--g);color:white;padding:1px 6px;border-radius:10px;font-size:.65rem;font-weight:800">FREE</span>' if ep_no <= 15 else ""
                        )
                        cliff_color = {"Slap":"#D32F2F","Reveal":"#7B68EE","Reversal":"#FF8C00",
                                       "Arrival":"#2EC484","Choice":"#191970","Threat":"#D32F2F","Tears":"#FF69B4"
                                      }.get(ep.get("cliffhanger_type",""), "#888")
                        sb = ep.get("sweet_bitter","")
                        sb_color = "#FF69B4" if "甜" in sb and "虐" not in sb else "#7B68EE" if "虐" in sb and "甜" not in sb else "#888"
                        d_m = ep.get("dopamine_moment", "")
                        table_rows += (
                            f'<tr style="border-bottom:1px solid #E6E9EF">'
                            f'<td style="padding:5px 8px;font-weight:700;white-space:nowrap">EP {ep_no} {badge}</td>'
                            f'<td style="padding:5px 8px;font-size:.82rem">{ep.get("summary","")}</td>'
                            f'<td style="padding:5px 8px;font-size:.75rem;color:{sb_color};text-align:center">{sb}</td>'
                            f'<td style="padding:5px 8px;font-size:.78rem;font-weight:700;color:{cliff_color};white-space:nowrap">{ep.get("cliffhanger_type","")}</td>'
                            f'<td style="padding:5px 8px;font-size:.75rem;color:var(--orange)">{d_m[:20] if d_m else ""}</td>'
                            f'</tr>'
                        )

                st.markdown(
                    f'<div style="overflow-x:auto;max-height:480px;overflow-y:auto">'
                    f'<table style="width:100%;border-collapse:collapse;font-family:var(--body)">'
                    f'<thead style="position:sticky;top:0;background:#191970">'
                    f'<tr><th style="padding:7px 8px;text-align:left;color:#FFCB05;font-size:.72rem">EP</th>'
                    f'<th style="padding:7px 8px;text-align:left;color:#FFCB05;font-size:.72rem">핵심 사건</th>'
                    f'<th style="padding:7px 8px;text-align:center;color:#FFCB05;font-size:.72rem">甜虐</th>'
                    f'<th style="padding:7px 8px;text-align:left;color:#FFCB05;font-size:.72rem">클리프행어</th>'
                    f'<th style="padding:7px 8px;text-align:left;color:#FFCB05;font-size:.72rem">🧠 도파민</th>'
                    f'</tr></thead>'
                    f'<tbody style="background:var(--card)">{table_rows}</tbody>'
                    f'</table></div>', unsafe_allow_html=True
                )

                # 다운로드
                arc_txt = f"BLUE JEANS SHORTFORM ENGINE v2.1 — {st.session_state.concept.get('title','')}\n"
                arc_txt += f"아크 요약: {arc.get('arc_summary','')}\n\n"
                for block in blocks:
                    arc_txt += f"[{block.get('ep_range','')} — {block.get('phase','')} / {block.get('sweet_bitter','')} / 도파민: {block.get('dopamine_target','')}]\n"
                    for ep in block.get("episodes", []):
                        arc_txt += f"  EP{ep.get('ep','')}: {ep.get('summary','')} | {ep.get('cliffhanger_type','')}: {ep.get('cliffhanger','')} | 🧠{ep.get('dopamine_moment','')}\n"
                    arc_txt += "\n"
                st.download_button("⬇️ 아크 + 도파민 설계 TXT",
                    arc_txt.encode("utf-8"),
                    file_name=f"arc_{st.session_state.concept.get('title','')}.txt",
                    mime="text/plain")

    # ── STEP 3: 집필 ──
    if st.session_state.step >= 2 and st.session_state.arc:
        st.markdown("---")
        st.markdown('<div class="section-header">STEP 3 &nbsp; 블록 집필 <span class="en">BLOCK WRITING</span></div>', unsafe_allow_html=True)
        st.caption("블록 1개 = 5화. 버튼 1클릭 = 5화 대본 생성 (스트리밍)")

        blocks = st.session_state.arc.get("blocks", [])
        for row_start in range(0, len(blocks), 5):
            cols = st.columns(5)
            for col_idx, col in enumerate(cols):
                bi = row_start + col_idx
                if bi >= len(blocks): break
                block = blocks[bi]
                bn = block.get("block_no", bi+1)
                ep_range = block.get("ep_range", "")
                is_done = bn in st.session_state.blocks
                is_paywall = bn in [4, 5]
                sw = block.get("sweet_bitter","")

                with col:
                    label = f"✓ 블록{bn}" if is_done else f"✍️ 블록{bn}"
                    pay_badge = " 💰" if is_paywall else ""
                    sw_badge = f" {sw}" if sw else ""
                    if st.button(f"{label}\n{ep_range}{pay_badge}{sw_badge}",
                                 key=f"b_{bn}", use_container_width=True):
                        prev_s = ""
                        if bn > 1 and (bn-1) in st.session_state.blocks:
                            t = st.session_state.blocks[bn-1]
                            prev_s = t[-300:] if len(t) > 300 else t
                        with st.spinner(f"블록 {bn} ({ep_range}) 집필 중... (Opus — 고품질 모드)"):
                            prompt_text = P.build_block_prompt(
                                st.session_state.concept, block, bn, prev_s)
                            result_text = ""
                            ph = st.empty()
                            for chunk in call_stream(prompt_text, MAX_TOKENS_BLOCK, model=MODEL_WRITE):
                                result_text += chunk
                                if len(result_text) % 200 < 10:
                                    ph.text_area(f"블록{bn} 생성 중...", result_text, height=150,
                                                  key=f"s_{bn}_{len(result_text)}")
                            st.session_state.blocks[bn] = result_text
                            st.rerun()

        # 집필된 블록 표시
        if st.session_state.blocks:
            st.markdown("---")
            st.markdown("#### 📝 집필된 대본")
            for bn in sorted(st.session_state.blocks.keys()):
                bt = st.session_state.blocks[bn]
                bi_info = blocks[bn-1] if bn <= len(blocks) else {}
                ep_range = bi_info.get("ep_range", f"블록{bn}")
                phase = bi_info.get("phase", "")
                sw = bi_info.get("sweet_bitter", "")
                dt = bi_info.get("dopamine_target", "")

                with st.expander(f"블록{bn} — {ep_range} [{phase}] {sw} 🧠{dt}",
                                  expanded=(bn == max(st.session_state.blocks.keys()))):
                    st.text_area("대본", bt, height=400, key=f"ta_{bn}")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.download_button(f"⬇️ 블록{bn} TXT", bt.encode("utf-8"),
                            file_name=f"block{bn:02d}_{ep_range.replace(' ','')}.txt",
                            mime="text/plain", key=f"dl_{bn}")
                    with c2:
                        if st.button(f"🗑️ 삭제", key=f"del_{bn}"):
                            del st.session_state.blocks[bn]
                            st.rerun()

    # ── STEP 4: 다운로드 ──
    if st.session_state.blocks:
        st.markdown("---")
        st.markdown('<div class="section-header">STEP 4 &nbsp; 다운로드 <span class="en">DOWNLOAD</span></div>', unsafe_allow_html=True)

        total_blocks = len(st.session_state.blocks)
        st.success(f"✅ {total_blocks}개 블록 완성 — 약 {total_blocks*5}화 대본")

        title = st.session_state.concept.get("title", "shortform") if st.session_state.concept else "shortform"
        full_txt = f"👖 BLUE JEANS SHORTFORM ENGINE v2.1\n제목: {title}\n"
        if st.session_state.concept:
            full_txt += f"로그라인: {st.session_state.concept.get('logline','')}\n"
            dd = st.session_state.concept.get("dopamine_design", {})
            full_txt += f"중독 루프: {dd.get('addiction_loop','')}\n"
        full_txt += f"생성일: {datetime.now().strftime('%Y-%m-%d')}\n{'='*60}\n\n"

        for bn in sorted(st.session_state.blocks.keys()):
            bi_info = (st.session_state.arc.get("blocks",[{}])[bn-1]
                       if st.session_state.arc and bn <= len(st.session_state.arc.get("blocks",[])) else {})
            ep_range = bi_info.get("ep_range", f"블록{bn}")
            full_txt += f"\n{'='*60}\n[블록{bn} — {ep_range}]\n{'='*60}\n\n"
            full_txt += st.session_state.blocks[bn] + "\n\n"

        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            st.download_button("📄 전체 대본 TXT", full_txt.encode("utf-8"),
                file_name=f"{title}_전체대본.txt", mime="text/plain", use_container_width=True)
        with col_dl2:
            if st.session_state.arc:
                csv = ["EP,핵심사건,甜虐,클리프행어유형,클리프행어,도파민,과금"]
                for block in st.session_state.arc.get("blocks",[]):
                    for ep in block.get("episodes",[]):
                        pay = "Y" if ep.get("ep",0) in st.session_state.arc.get("paywall_eps",[]) else "N"
                        csv.append(f"EP{ep.get('ep','')},{ep.get('summary','').replace(',','；')},"
                                   f"{ep.get('sweet_bitter','')},{ep.get('cliffhanger_type','')},"
                                   f"{ep.get('cliffhanger','').replace(',','；')},"
                                   f"{ep.get('dopamine_moment','').replace(',','；')},{pay}")
                st.download_button("📊 아크 CSV", "\n".join(csv).encode("utf-8-sig"),
                    file_name=f"{title}_아크.csv", mime="text/csv", use_container_width=True)
        with col_dl3:
            if st.button("🔄 전체 초기화", use_container_width=True):
                for k in ["step","concept","arc","blocks","convert_result"]:
                    st.session_state[k] = 0 if k=="step" else {} if k=="blocks" else None
                st.rerun()


# ═══════════════════════════════════════════════════
#  TAB 2: 기존 글 → 숏폼 변환
# ═══════════════════════════════════════════════════
with tab_convert:
    st.markdown("---")
    st.markdown('<div class="section-header">🔄 기존 글 → 숏폼 변환 <span class="en">CONVERT TO SHORTFORM</span></div>', unsafe_allow_html=True)
    st.caption("소설, 시나리오, 웹툰, 실화 등 어떤 텍스트든 도파민 설계가 탑재된 숏폼으로 변환.")

    col_cv1, col_cv2 = st.columns([2, 1])
    with col_cv1:
        source_text = st.text_area("원본 텍스트 붙여넣기",
            placeholder="소설 일부, 시나리오, 기사, 줄거리 등 최대 3,000자.",
            height=160)
        preserve_elements = st.text_area("보존할 원작 요소 (선택)",
            placeholder="원작에서 반드시 살릴 감성/설정/캐릭터\n예: 단짠단짠 감성, 취준생 현실감, 캠퍼스+오피스 교차",
            height=65)
    with col_cv2:
        cv_formula = st.selectbox("막장 공식",
            list(P.MAKJANG_FORMULAS.keys()),
            format_func=lambda x: P.MAKJANG_FORMULAS[x]["name"], key="cvf")
        cv_intensity = st.selectbox("변환 강도",
            list(P.CONVERT_INTENSITY.keys()),
            format_func=lambda x: P.CONVERT_INTENSITY[x]["name"],
            index=2, key="cvi")
        col_m2, col_r2 = st.columns(2)
        with col_m2:
            cv_market = st.selectbox("시장", ["한국","글로벌","중국"], key="cvm")
        with col_r2:
            cv_rating = st.selectbox("수위",
                ["family","teen","adult"],
                format_func=lambda x: {"family":"전체가","teen":"15세+","adult":"19+"}[x],
                index=1, key="cvr")
        cv_eps = st.selectbox("목표 화수", [20,30,50,100], index=1, key="cve")

        intensity_info = P.CONVERT_INTENSITY[cv_intensity]
        st.markdown(
            f'<div class="ri" style="border-left:3px solid var(--orange)">'
            f'<div class="rl" style="color:var(--orange)">변환 강도</div>'
            f'<div style="font-size:.75rem">{intensity_info["desc"]}</div>'
            f'</div>', unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="ri" style="border-left:3px solid var(--orange)">'
            f'<div class="rl" style="color:var(--orange)">🧠 도파민</div>'
            f'<div style="font-size:.75rem">{P.MAKJANG_FORMULAS[cv_formula]["dopamine_key"][:60]}...</div>'
            f'</div>', unsafe_allow_html=True
        )

    if st.button("🔄 도파민 탑재 숏폼으로 변환", type="primary", use_container_width=True, key="btn_cv"):
        if not source_text.strip():
            st.error("원본 텍스트를 입력하세요.")
        else:
            with st.spinner("원본 분석 + 도파민 설계 + 숏폼 변환 중... (40~60초)"):
                raw = call_claude(
                    P.build_convert_prompt(source_text, cv_formula, cv_eps,
                                           cv_intensity, preserve_elements, cv_market, cv_rating),
                    MAX_TOKENS_CONVERT
                )
                result = safe_json(raw)
                if result:
                    st.session_state.convert_result = result
                    st.rerun()
                else:
                    st.error("변환 실패.")
                    with st.expander("Raw"): st.text(raw[:2000])

    if st.session_state.convert_result:
        cr = st.session_state.convert_result
        st.markdown("---")

        # 원본 분석
        oa = cr.get("original_analysis", {})
        st.markdown("#### 📖 원본 분석")
        col_oa1, col_oa2 = st.columns(2)
        with col_oa1:
            st.markdown(f'<div class="ri"><div class="rl">핵심 갈등</div>{oa.get("core_conflict","")}</div>', unsafe_allow_html=True)
            if oa.get("dopamine_potential"):
                st.markdown(f'<div class="ri" style="border-left:3px solid var(--orange)"><div class="rl" style="color:var(--orange)">🧠 도파민 잠재력</div>{oa["dopamine_potential"]}</div>', unsafe_allow_html=True)
            if oa.get("usable_elements"):
                elem = "".join([f'<div style="font-size:.85rem;margin:.2rem 0">✓ {e}</div>' for e in oa["usable_elements"]])
                st.markdown(f'<div class="ri"><div class="rl">활용 가능 요소</div>{elem}</div>', unsafe_allow_html=True)
        with col_oa2:
            if oa.get("preserved_elements"):
                pres = "".join([f'<div style="font-size:.85rem;margin:.2rem 0">♻ {e}</div>' for e in oa["preserved_elements"]])
                st.markdown(f'<div class="ri" style="border-left:3px solid var(--g)"><div class="rl" style="color:var(--g)">보존 요소</div>{pres}</div>', unsafe_allow_html=True)
            if oa.get("problems"):
                prob = "".join([f'<div style="font-size:.85rem;margin:.2rem 0;color:var(--r)">✗ {p}</div>' for p in oa["problems"]])
                st.markdown(f'<div class="ri"><div class="rl">숏폼 부적합 이유</div>{prob}</div>', unsafe_allow_html=True)

        # 변환 전략
        cs = cr.get("conversion_strategy", {})
        st.markdown("#### ⚡ 변환 전략 + 도파민 설계")
        col_cs1, col_cs2 = st.columns(2)
        with col_cs1:
            st.markdown(f'<div class="card" style="border-left:4px solid var(--y)"><div class="cl">주인공 재설계 (낙차 극대화)</div>{cs.get("protagonist_rewrite","")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card" style="border-left:4px solid var(--r)"><div class="cl">악역 설계 (구체적 나쁜 짓)</div>{cs.get("villain_injection","")}</div>', unsafe_allow_html=True)
            if cs.get("hidden_identity"):
                st.markdown(f'<div class="ri"><div class="rl">🎭 숨겨진 정체 (隐身)</div>{cs["hidden_identity"]}</div>', unsafe_allow_html=True)
        with col_cs2:
            dd_cv = cs.get("dopamine_design", {})
            if dd_cv:
                st.markdown(
                    f'<div class="card" style="border-left:4px solid var(--orange)">'
                    f'<div class="cl">🧠 도파민 설계</div>'
                    f'<div style="font-size:.85rem;margin:.3rem 0">주력: {dd_cv.get("primary_trigger","")}</div>'
                    f'<div style="font-size:.85rem;margin:.3rem 0">루프: {dd_cv.get("addiction_loop","")}</div>'
                    f'<div style="font-size:.85rem;margin:.3rem 0">역전: {dd_cv.get("reversal_timing","")}</div>'
                    f'<div style="font-size:.85rem;margin:.3rem 0">시소: {dd_cv.get("seesaw","")}</div>'
                    f'</div>', unsafe_allow_html=True
                )
            if cs.get("paywall_moment"):
                st.markdown(f'<div class="card" style="border-left:4px solid var(--y);background:#FFFEF0"><div class="cl">💰 과금 전환점</div>{cs["paywall_moment"]}</div>', unsafe_allow_html=True)

        # 숏폼 컨셉
        sc = cr.get("shortform_concept", {})
        if sc:
            st.markdown("#### 🎬 숏폼 컨셉")
            st.markdown(f'<div class="callout"><div class="cl">{sc.get("title","")} — 로그라인</div>{sc.get("logline","")}</div>', unsafe_allow_html=True)
            col_sc1, col_sc2 = st.columns(2)
            with col_sc1:
                st.markdown(f'<div class="ri"><div class="rl">EP1 첫 프레임</div>{sc.get("hook_ep1","")}</div>', unsafe_allow_html=True)
                if sc.get("first_subtitle"):
                    st.markdown(f'<div class="ri" style="border-left:3px solid var(--orange)"><div class="rl" style="color:var(--orange)">📱 첫 자막</div>{sc["first_subtitle"]}</div>', unsafe_allow_html=True)
            with col_sc2:
                st.markdown(f'<div class="ri"><div class="rl">甜虐 감정 곡선</div>{sc.get("emotional_arc","")}</div>', unsafe_allow_html=True)
                if sc.get("china_hook"):
                    st.markdown(f'<div class="ri" style="border-left:3px solid #D32F2F"><div class="rl" style="color:#D32F2F">🇨🇳 중국 훅</div>{sc["china_hook"]}</div>', unsafe_allow_html=True)

        # EP 맵
        ep_map = cr.get("episode_map", [])
        if ep_map:
            st.markdown("#### 📊 에피소드 맵")
            ep_html = ""
            for ep in ep_map:
                cc = {"Slap":"#D32F2F","Reveal":"#7B68EE","Reversal":"#FF8C00",
                      "Arrival":"#2EC484","Choice":"#191970","Threat":"#D32F2F","Tears":"#FF69B4"
                     }.get(ep.get("cliff_type",""), "#888")
                sb = ep.get("sweet_bitter","")
                sc_c = "#FF69B4" if "甜" in sb and "虐" not in sb else "#7B68EE" if "虐" in sb and "甜" not in sb else "#888"
                d_badge = dopamine_badge(ep.get("dopamine",""))
                ep_html += (
                    f'<div style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #E6E9EF">'
                    f'<div style="min-width:90px;font-weight:700;font-size:.82rem;color:var(--navy)">{ep.get("ep_range","")}</div>'
                    f'<div style="flex:1;font-size:.82rem">{ep.get("summary","")}</div>'
                    f'<div style="min-width:30px;text-align:center;font-size:.72rem;color:{sc_c}">{sb}</div>'
                    f'<div style="min-width:60px;text-align:right;font-size:.75rem;font-weight:700;color:{cc}">{ep.get("cliff_type","")}</div>'
                    f'<div>{d_badge}</div>'
                    f'</div>'
                )
            st.markdown(f'<div class="card">{ep_html}</div>', unsafe_allow_html=True)

        # 파일럿 EP1 + EP2
        pilot1 = cr.get("pilot_ep1", "")
        pilot2 = cr.get("pilot_ep2", "")
        if pilot1:
            st.markdown("#### 🎬 파일럿 대본")
            t1, t2 = st.tabs(["EP 1", "EP 2"])
            with t1:
                st.markdown(
                    f'<div class="ep-block"><div class="ep-header">EP 1 — 파일럿 (도파민 설계 탑재)</div>'
                    f'<pre style="white-space:pre-wrap;font-family:var(--body);font-size:.9rem;line-height:1.8">{pilot1}</pre>'
                    f'</div>', unsafe_allow_html=True
                )
            with t2:
                if pilot2:
                    st.markdown(
                        f'<div class="ep-block"><div class="ep-header">EP 2</div>'
                        f'<pre style="white-space:pre-wrap;font-family:var(--body);font-size:.9rem;line-height:1.8">{pilot2}</pre>'
                        f'</div>', unsafe_allow_html=True
                    )
                else:
                    st.caption("EP 2가 생성되지 않았습니다. 다시 변환을 실행하세요.")

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                out = f"BLUE JEANS SHORTFORM ENGINE v2.1 — 변환 결과\n"
                out += f"제목: {sc.get('title','')}\n로그라인: {sc.get('logline','')}\n\n"
                out += f"[파일럿 EP1]\n{pilot1}\n\n[파일럿 EP2]\n{pilot2}"
                st.download_button("⬇️ 파일럿 대본 TXT", out.encode("utf-8"),
                    file_name=f"pilot_{sc.get('title','convert')}.txt",
                    mime="text/plain", use_container_width=True)
            with col_dl2:
                if st.button("이 컨셉으로 100화 만들기 →", use_container_width=True, key="cv_to_full"):
                    st.session_state.concept = {
                        "title": sc.get("title",""),
                        "logline": sc.get("logline",""),
                        "formula": cv_formula,
                        "market": cv_market,
                        "rating": cv_rating,
                        "season_question": sc.get("logline",""),
                        "protagonist": {"name":"주인공","age":"","arc":sc.get("emotional_arc",""),
                                        "identity":"","hidden_power":cs.get("hidden_identity",""),
                                        "secret":"","dialogue_tone":"","start_state":"","scroll_stop":""},
                        "villain": {"name":"악역","age":"","identity":"",
                                    "specific_evil":cs.get("villain_injection",""),
                                    "why_hateful":"","secret":"","dialogue_tone":"","downfall":""},
                        "helper": {"name":"","role":"","hidden_agenda":"","twist_ep":""},
                        "rival": {"name":"","role":"","advantage":"","purpose":""},
                        "dopamine_design": dd_cv if dd_cv else {},
                        "secrets": [],
                        "paywall_design": {"ep16_reversal":cs.get("paywall_moment",""),"ep16_dopamine":"","ep16_china":"","ep20_cliffhanger":""},
                        "location_design": {"main_locations":[],"sub_locations":[],"reversal_location":"","cliffhanger_location":"","romance_peak":""},
                        "hook_sentence": sc.get("hook_ep1",""),
                        "first_subtitle": sc.get("first_subtitle",""),
                        "total_eps": 100
                    }
                    st.session_state.step = 1
                    st.success("컨셉 설정 완료. STEP 2 탭에서 아크를 생성하세요.")

st.markdown(
    '<div style="text-align:center;font-size:0.65rem;padding:30px 0 16px;letter-spacing:2px;opacity:0.25;">'
    '© 2026 BLUE JEANS PICTURES · Shortform Engine v2.1 · Opus(집필) + Sonnet(설계)'
    '</div>', unsafe_allow_html=True
)
