"""
👖 BLUE JEANS SHORTFORM ENGINE v1.0 — main.py
막장 공식 + 1분 클리프행어 + 과금 전환점
© 2026 BLUE JEANS PICTURES
"""

import streamlit as st
import anthropic
import json
import re
import io
from datetime import datetime
import prompt as P

# ─── 모델 설정 ───
MODEL = "claude-sonnet-4-6"   # 숏폼은 속도 우선 — Sonnet으로 충분
MAX_TOKENS_CONCEPT = 4000
MAX_TOKENS_ARC = 16000
MAX_TOKENS_BLOCK = 8000
MAX_TOKENS_CONVERT = 8000

# ─── Page Config ───
st.set_page_config(
    page_title="BLUE JEANS · Shortform Engine",
    page_icon="👖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CSS ───
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@latest/Paperlogy.css');
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&display=swap');

:root {
    --navy: #191970;
    --y: #FFCB05;
    --bg: #F7F7F5;
    --card: #FFFFFF;
    --card-border: #E2E2E0;
    --t: #1A1A2E;
    --r: #D32F2F;
    --g: #2EC484;
    --dim: #8E8E99;
    --light-bg: #EEEEF6;
    --orange: #FF6B35;
    --body: 'Pretendard', -apple-system, sans-serif;
    --heading: 'Paperlogy', 'Pretendard', sans-serif;
    --display: 'Playfair Display', 'Paperlogy', serif;
}
html, body, [class*="css"] { font-family: var(--body); color: var(--t); -webkit-font-smoothing: antialiased; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stMainBlockContainer"], [data-testid="stHeader"], [data-testid="stBottom"] {
    background-color: var(--bg) !important; color: var(--t) !important;
}
.stMarkdown, .stText { color: var(--t) !important; }
h1,h2,h3,h4,h5,h6 { color: var(--navy) !important; font-family: var(--heading) !important; }
section[data-testid="stSidebar"] { display: none; }

/* 입력 위젯 */
.stTextInput input, .stTextArea textarea,
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
    background-color: var(--card) !important; color: var(--t) !important;
    border: 1.5px solid var(--card-border) !important; border-radius: 8px !important;
    font-family: var(--body) !important; font-size: 0.9rem !important;
    padding: 0.6rem 0.8rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--navy) !important;
    box-shadow: 0 0 0 2px rgba(25,25,112,0.08) !important;
}
.stSelectbox > div > div, [data-baseweb="select"] > div {
    background-color: var(--card) !important; color: var(--t) !important;
    border-color: var(--card-border) !important; border-radius: 8px !important;
}
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [role="option"] {
    background-color: var(--card) !important; color: var(--t) !important;
}
[role="option"]:hover { background-color: var(--light-bg) !important; }
.stTextInput label, .stTextArea label, .stSelectbox label {
    color: var(--t) !important; font-weight: 600 !important;
    font-size: 0.82rem !important;
}

/* 버튼 */
.stButton > button {
    color: var(--t) !important; border: 1.5px solid var(--card-border) !important;
    background-color: var(--card) !important; border-radius: 8px !important;
    font-family: var(--body) !important; font-weight: 600 !important;
    font-size: 0.85rem !important; padding: 0.5rem 1.2rem !important;
    transition: all 0.2s;
}
.stButton > button:hover { border-color: var(--navy) !important; }
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background-color: var(--y) !important; color: var(--navy) !important;
    border-color: var(--y) !important; font-weight: 700 !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #E8B800 !important;
    box-shadow: 0 2px 12px rgba(255,203,5,0.3) !important;
}

/* 다운로드 버튼 */
[data-testid="stDownloadButton"] button {
    background-color: var(--navy) !important; color: white !important;
    border-color: var(--navy) !important; font-weight: 700 !important;
}

/* Expander */
.stExpander details summary {
    background-color: var(--card) !important; color: var(--t) !important;
    border: 1px solid var(--card-border) !important; border-radius: 8px !important;
}
details[open] > div { background-color: var(--card) !important; }

/* Alert */
.stAlert { border-radius: 8px !important; }
[data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"],
[data-testid="stColumn"] { background-color: transparent !important; }
.stCaption, small { color: var(--dim) !important; }

/* 브랜드 */
.header { font-size:0.85rem; font-weight:700; color:var(--navy); letter-spacing:0.15em; font-family:var(--heading); }
.brand-title { font-size:2.6rem; font-weight:900; color:var(--navy); font-family:var(--display); letter-spacing:-0.02em; }
.sub { font-size:0.72rem; font-weight:600; letter-spacing:0.18em; color:var(--dim); }

/* 카드 */
.card { background:var(--card); border:1px solid var(--card-border); border-radius:12px;
    padding:1.2rem 1.4rem; margin-bottom:1rem; }
.callout { background:var(--light-bg); border-left:4px solid var(--y);
    border-radius:0 8px 8px 0; padding:0.8rem 1rem; margin-bottom:0.8rem; }
.cl { font-size:0.72rem; font-weight:700; color:var(--navy); letter-spacing:0.08em;
    text-transform:uppercase; margin-bottom:0.3rem; }
.section-header { font-size:1.05rem; font-weight:800; color:var(--navy);
    font-family:var(--heading); padding:0.5rem 0; border-bottom:2px solid var(--y);
    margin-bottom:1rem; }
.en { font-size:0.7rem; font-weight:600; color:var(--dim); letter-spacing:0.1em; margin-left:0.5rem; }
.ri { background:var(--card); border:1px solid var(--card-border); border-left:3px solid var(--navy);
    border-radius:0 8px 8px 0; padding:0.7rem 1rem; margin-bottom:0.5rem; }
.rl { font-size:0.7rem; font-weight:700; color:var(--dim); margin-bottom:0.2rem; }
.big { font-size:3rem; font-weight:900; color:var(--navy); line-height:1; }
.sm { font-size:0.8rem; font-weight:700; color:var(--dim); }

/* 막장 공식 카드 */
.formula-card { background:var(--card); border:2px solid var(--card-border);
    border-radius:12px; padding:1rem 1.2rem; cursor:pointer; transition:all 0.2s;
    margin-bottom:0.5rem; }
.formula-card:hover { border-color:var(--y); }
.formula-card.selected { border-color:var(--y); background:#FFFEF0; }

/* EP 대본 */
.ep-block { background:var(--card); border:1px solid var(--card-border);
    border-left:4px solid var(--orange); border-radius:0 12px 12px 0;
    padding:1.2rem 1.4rem; margin-bottom:1rem; }
.ep-header { font-size:0.9rem; font-weight:800; color:var(--orange);
    letter-spacing:0.05em; margin-bottom:0.8rem; }
.cliff-badge { display:inline-block; background:var(--r); color:white;
    padding:2px 10px; border-radius:20px; font-size:0.7rem; font-weight:800;
    margin-left:0.5rem; }
.paywall-badge { display:inline-block; background:var(--y); color:var(--navy);
    padding:2px 10px; border-radius:20px; font-size:0.7rem; font-weight:800;
    margin-left:0.5rem; }
.free-badge { display:inline-block; background:var(--g); color:white;
    padding:2px 10px; border-radius:20px; font-size:0.7rem; font-weight:800; }

/* 스텝 바 */
.step-bar { display:flex; align-items:center; justify-content:center;
    gap:0; margin:1.5rem 0; }
.step-dot { width:34px; height:34px; border-radius:50%; display:flex;
    align-items:center; justify-content:center; font-weight:900; font-size:0.8rem; }
.step-dot.done { background:var(--g); color:white; }
.step-dot.active { background:var(--y); color:var(--navy); }
.step-dot.wait { background:#E6E9EF; color:#AAA; }
.step-line { flex:1; height:2px; background:#E6E9EF; max-width:80px; }
.step-line.done { background:var(--g); }

hr { border-color: var(--card-border) !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
#  세션 초기화
# ═══════════════════════════════════════════════════

def init_session():
    defaults = {
        "step": 0,           # 0: 컨셉, 1: 아크, 2: 집필, 3: 변환
        "mode": "create",    # create | convert
        "concept": None,
        "arc": None,
        "blocks": {},        # {block_no: text}
        "convert_result": None,
        "formula": "재벌복수",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ═══════════════════════════════════════════════════
#  유틸리티
# ═══════════════════════════════════════════════════

def get_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("ANTHROPIC_API_KEY가 secrets에 없습니다.")
        st.stop()
    return anthropic.Anthropic(api_key=api_key)

def safe_json(text: str):
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        try:
            cleaned = re.sub(r'```json\s*|```\s*', '', text).strip()
            return json.loads(cleaned)
        except Exception:
            return None

def call_claude(prompt: str, max_tokens: int, system: str = "") -> str:
    client = get_client()
    msgs = [{"role": "user", "content": prompt}]
    kwargs = {"model": MODEL, "max_tokens": max_tokens, "messages": msgs}
    if system:
        kwargs["system"] = system
    resp = client.messages.create(**kwargs)
    return "".join(b.text for b in resp.content if hasattr(b, "text")).strip()

def call_claude_stream(prompt: str, max_tokens: int, system: str = ""):
    client = get_client()
    msgs = [{"role": "user", "content": prompt}]
    kwargs = {"model": MODEL, "max_tokens": max_tokens, "messages": msgs}
    if system:
        kwargs["system"] = system
    with client.messages.stream(**kwargs) as stream:
        for text in stream.text_stream:
            yield text

def render_step_bar(current_step: int, mode: str = "create"):
    if mode == "convert":
        labels = ["원본 분석", "숏폼 변환 결과"]
        dots = ""
        for i, label in enumerate(labels):
            s = current_step - 3
            cls = "done" if s > i else ("active" if s == i else "wait")
            sym = "✓" if s > i else str(i + 1)
            dots += (f'<div style="display:flex;flex-direction:column;align-items:center;gap:5px;">'
                     f'<div class="step-dot {cls}">{sym}</div>'
                     f'<div style="font-size:0.68rem;opacity:0.65;white-space:nowrap;">{label}</div></div>')
            if i < len(labels) - 1:
                lc = "done" if s > i else ""
                dots += f'<div class="step-line {lc}"></div>'
    else:
        labels = ["컨셉 설정", "100화 아크", "블록 집필", "다운로드"]
        dots = ""
        for i, label in enumerate(labels):
            cls = "done" if current_step > i else ("active" if current_step == i else "wait")
            sym = "✓" if current_step > i else str(i + 1)
            dots += (f'<div style="display:flex;flex-direction:column;align-items:center;gap:5px;">'
                     f'<div class="step-dot {cls}">{sym}</div>'
                     f'<div style="font-size:0.68rem;opacity:0.65;white-space:nowrap;">{label}</div></div>')
            if i < len(labels) - 1:
                lc = "done" if current_step > i else ""
                dots += f'<div class="step-line {lc}"></div>'
    st.markdown(f'<div class="step-bar">{dots}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
#  브랜드 헤더
# ═══════════════════════════════════════════════════

st.markdown(
    '<div style="text-align:center;padding:1rem 0 0 0">'
    '<div class="header">B L U E &nbsp; J E A N S &nbsp; P I C T U R E S</div>'
    '<div class="brand-title">SHORTFORM ENGINE</div>'
    '<div class="sub">M A K J A N G &nbsp; · &nbsp; 1 0 0 E P &nbsp; · &nbsp; C L I F F H A N G E R &nbsp; · &nbsp; P A Y W A L L</div>'
    '</div>',
    unsafe_allow_html=True
)
st.caption(f"Model: {MODEL} · 22클릭 → 100화 완성")

# 모드 탭
tab_create, tab_convert = st.tabs(["✍️ 새 숏폼 만들기", "🔄 기존 글 → 숏폼 변환"])


# ═══════════════════════════════════════════════════
#  TAB 1: 새 숏폼 만들기
# ═══════════════════════════════════════════════════

with tab_create:
    render_step_bar(st.session_state.step, "create")
    st.markdown('<hr>', unsafe_allow_html=True)

    # ─────────────────────────────────────
    # STEP 1: 컨셉 설정
    # ─────────────────────────────────────
    st.markdown('<div class="section-header">STEP 1 &nbsp; 컨셉 설정 <span class="en">CONCEPT SETUP</span></div>', unsafe_allow_html=True)

    col_f1, col_f2 = st.columns(2)

    formula_options = {
        "재벌복수": "👑 재벌 복수 — 신분 격차 + 출생의 비밀 + 지위 역전",
        "능력각성": "⚡ 능력 각성 — 무시당한 주인공의 숨겨진 능력",
        "귀환재회": "🔄 귀환 / 재회 — 5년 후 돌아온 사람 + 아이의 정체",
        "복수극":   "🗡️ 복수극 — 배신당함 → 하나씩 무너뜨리기",
    }

    with col_f1:
        formula_key = st.selectbox(
            "막장 공식 선택",
            list(formula_options.keys()),
            format_func=lambda x: formula_options[x],
            key="formula_select"
        )
        st.session_state.formula = formula_key
        formula = P.MAKJANG_FORMULAS[formula_key]
        st.markdown(
            f'<div class="callout"><div class="cl">공식 설명</div>'
            f'{formula["desc"]}<br>'
            f'<span style="font-size:.8rem;color:var(--navy);font-weight:700">💰 과금 포인트:</span>'
            f'<span style="font-size:.8rem"> {formula["paywall"]}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_f2:
        total_eps = st.selectbox("총 에피소드 수", [80, 90, 100], index=2)
        custom_idea = st.text_area("커스텀 아이디어 (선택)", placeholder="공식을 변형하거나 특별한 설정이 있으면 입력", height=80)

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        protagonist = st.text_area(
            "주인공 설정",
            placeholder="이름 / 나이 / 직업\n처한 상황 (최대한 불쌍하게)\n숨겨진 정체 또는 능력",
            height=100
        )
        secrets = st.text_area(
            "핵심 비밀 2~3개",
            placeholder="비밀1: EP__에서 드러남 — 내용\n비밀2: EP__에서 드러남 — 내용\n비밀3: EP__에서 드러남 — 내용",
            height=100
        )
    with col_i2:
        villain = st.text_area(
            "메인 악역 설정",
            placeholder="이름 / 나이 / 직업\n관객이 분노하는 행동\n숨겨진 비밀 또는 약점",
            height=100
        )
        season_question = st.text_input(
            "시즌 질문 (이 드라마의 핵심 질문 1줄)",
            placeholder="예: 이 여자는 진짜 재벌 딸인가, 복수에 성공할 것인가?"
        )

    if st.button("🧠 컨셉 생성", type="primary", use_container_width=True):
        if not protagonist or not villain or not season_question:
            st.error("주인공 / 악역 / 시즌 질문을 모두 입력하세요.")
        else:
            with st.spinner("컨셉 설계 중... (20~30초)"):
                prompt_text = P.build_concept_prompt(
                    formula_key, protagonist, villain,
                    secrets or "자동 생성", season_question, custom_idea
                )
                raw = call_claude(prompt_text, MAX_TOKENS_CONCEPT)
                result = safe_json(raw)
                if result:
                    st.session_state.concept = result
                    st.session_state.concept["total_eps"] = total_eps
                    st.session_state.step = 1
                    st.rerun()
                else:
                    st.error("컨셉 생성 실패. 다시 시도하세요.")
                    with st.expander("Raw"):
                        st.text(raw[:1000])

    # 컨셉 결과 표시
    if st.session_state.concept:
        c = st.session_state.concept
        st.markdown("---")
        st.markdown(f'<div class="section-header">📋 컨셉 결과: {c.get("title","")}</div>', unsafe_allow_html=True)

        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            st.markdown(
                f'<div class="callout"><div class="cl">로그라인</div>{c.get("logline","")}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="callout"><div class="cl">시즌 질문</div>{c.get("season_question","")}</div>',
                unsafe_allow_html=True
            )
        with col_c2:
            st.markdown(
                f'<div class="ri"><div class="rl">Hook 첫 대사</div>{c.get("hook_sentence","")}</div>',
                unsafe_allow_html=True
            )

        col_p, col_v = st.columns(2)
        with col_p:
            p = c.get("protagonist", {})
            st.markdown(
                f'<div class="card"><div class="cl">🔥 주인공: {p.get("name","")} ({p.get("age","")})</div>'
                f'<div style="font-size:.85rem">{p.get("identity","")}</div>'
                f'<div style="font-size:.8rem;color:var(--dim);margin-top:.4rem">비밀: {p.get("secret","")}</div>'
                f'<div style="font-size:.8rem;color:var(--g);margin-top:.3rem">아크: {p.get("arc","")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with col_v:
            v = c.get("villain", {})
            st.markdown(
                f'<div class="card" style="border-left:4px solid var(--r)"><div class="cl">🖤 악역: {v.get("name","")} ({v.get("age","")})</div>'
                f'<div style="font-size:.85rem">{v.get("identity","")}</div>'
                f'<div style="font-size:.8rem;color:var(--r);margin-top:.4rem">밉상 이유: {v.get("why_hateful","")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        # 과금 설계
        pd = c.get("paywall_design", {})
        st.markdown(
            f'<div class="card" style="border-left:4px solid var(--y)">'
            f'<div class="cl">💰 과금 전환점 설계 (EP 16~20)</div>'
            f'<div style="font-size:.9rem;font-weight:700">EP 16 대반전: {pd.get("ep16_reversal","")}</div>'
            f'<div style="font-size:.85rem;color:var(--dim);margin-top:.3rem">EP 20 클리프행어: {pd.get("ep20_cliffhanger","")}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # 비밀들
        secrets_data = c.get("secrets", [])
        if secrets_data:
            s_html = "".join([
                f'<div style="font-size:.85rem;margin:.3rem 0">• EP{s.get("reveal_ep","?")} — {s.get("secret","")} → {s.get("impact","")}</div>'
                for s in secrets_data if s.get("secret")
            ])
            st.markdown(
                f'<div class="ri"><div class="rl">🔒 비밀 공개 스케줄</div>{s_html}</div>',
                unsafe_allow_html=True
            )

    # ─────────────────────────────────────
    # STEP 2: 100화 아크
    # ─────────────────────────────────────
    if st.session_state.step >= 1 and st.session_state.concept:
        st.markdown("---")
        st.markdown('<div class="section-header">STEP 2 &nbsp; 100화 아크 설계 <span class="en">SEASON ARC</span></div>', unsafe_allow_html=True)

        if st.button("📊 아크 생성", type="primary", use_container_width=True):
            total = st.session_state.concept.get("total_eps", 100)
            with st.spinner(f"100화 아크 설계 중... (40~60초)"):
                prompt_text = P.build_arc_prompt(st.session_state.concept, total)
                raw = call_claude(prompt_text, MAX_TOKENS_ARC)
                result = safe_json(raw)
                if result:
                    st.session_state.arc = result
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.error("아크 생성 실패. 다시 시도하세요.")
                    with st.expander("Raw"):
                        st.text(raw[:2000])

        if st.session_state.arc:
            arc = st.session_state.arc
            st.markdown(
                f'<div class="callout"><div class="cl">아크 요약</div>{arc.get("arc_summary","")}</div>',
                unsafe_allow_html=True
            )

            # 100화 테이블
            blocks = arc.get("blocks", [])
            if blocks:
                # 테이블 렌더링
                table_rows = ""
                for block in blocks:
                    for ep in block.get("episodes", []):
                        ep_no = ep.get("ep", 0)
                        is_paywall = ep_no in arc.get("paywall_eps", [16,17,18,19,20])
                        is_free = ep_no <= 15
                        badge = ""
                        if is_paywall:
                            badge = '<span class="paywall-badge">💰 과금</span>'
                        elif is_free:
                            badge = '<span class="free-badge">FREE</span>'

                        cliff_color = {
                            "Slap":"#D32F2F","Reveal":"#7B68EE","Reversal":"#FF8C00",
                            "Arrival":"#2EC484","Choice":"#191970","Threat":"#D32F2F","Tears":"#FF69B4"
                        }.get(ep.get("cliffhanger_type",""), "#888")

                        emotion_emoji = {
                            "분노":"🔥","통쾌":"⚡","충격":"💥","감동":"💧","긴장":"😰"
                        }.get(ep.get("emotion",""), "")

                        table_rows += (
                            f'<tr style="border-bottom:1px solid #E6E9EF">'
                            f'<td style="padding:6px 10px;font-weight:700;white-space:nowrap">EP {ep_no} {badge}</td>'
                            f'<td style="padding:6px 10px;font-size:.85rem">{ep.get("summary","")}</td>'
                            f'<td style="padding:6px 10px;white-space:nowrap">'
                            f'<span style="color:{cliff_color};font-size:.8rem;font-weight:700">{ep.get("cliffhanger_type","")}</span>'
                            f'</td>'
                            f'<td style="padding:6px 10px;font-size:.82rem;color:var(--dim)">{ep.get("cliffhanger","")}</td>'
                            f'<td style="padding:6px 10px;text-align:center">{emotion_emoji}</td>'
                            f'</tr>'
                        )

                st.markdown(
                    f'<div style="overflow-x:auto;max-height:500px;overflow-y:auto">'
                    f'<table style="width:100%;border-collapse:collapse;font-family:var(--body)">'
                    f'<thead style="position:sticky;top:0;background:#191970">'
                    f'<tr>'
                    f'<th style="padding:8px 10px;text-align:left;color:#FFCB05;font-size:.75rem">EP</th>'
                    f'<th style="padding:8px 10px;text-align:left;color:#FFCB05;font-size:.75rem">핵심 사건</th>'
                    f'<th style="padding:8px 10px;text-align:left;color:#FFCB05;font-size:.75rem">클리프행어</th>'
                    f'<th style="padding:8px 10px;text-align:left;color:#FFCB05;font-size:.75rem">내용</th>'
                    f'<th style="padding:8px 10px;text-align:center;color:#FFCB05;font-size:.75rem">감정</th>'
                    f'</tr></thead>'
                    f'<tbody style="background:var(--card)">{table_rows}</tbody>'
                    f'</table></div>',
                    unsafe_allow_html=True
                )

                # 아크 TXT 다운로드
                arc_txt = f"BLUE JEANS SHORTFORM ENGINE — {st.session_state.concept.get('title','')}\n"
                arc_txt += f"시즌 아크 요약: {arc.get('arc_summary','')}\n\n"
                for block in blocks:
                    arc_txt += f"[{block.get('ep_range','')} — {block.get('phase','')}] {block.get('theme','')}\n"
                    for ep in block.get("episodes", []):
                        arc_txt += f"  EP{ep.get('ep','')}: {ep.get('summary','')} | {ep.get('cliffhanger_type','')}: {ep.get('cliffhanger','')}\n"
                    arc_txt += "\n"

                st.download_button(
                    "⬇️ 아크 TXT 저장",
                    arc_txt.encode("utf-8"),
                    file_name=f"arc_{st.session_state.concept.get('title','shortform')}.txt",
                    mime="text/plain"
                )

    # ─────────────────────────────────────
    # STEP 3: 블록 집필
    # ─────────────────────────────────────
    if st.session_state.step >= 2 and st.session_state.arc:
        st.markdown("---")
        st.markdown('<div class="section-header">STEP 3 &nbsp; 블록 집필 <span class="en">BLOCK WRITING</span></div>', unsafe_allow_html=True)
        st.caption("블록 1개 = 5화. 버튼 한 번 클릭으로 5화 대본 생성.")

        blocks = st.session_state.arc.get("blocks", [])
        cols_per_row = 5
        for row_start in range(0, len(blocks), cols_per_row):
            cols = st.columns(cols_per_row)
            for col_idx, col in enumerate(cols):
                block_idx = row_start + col_idx
                if block_idx >= len(blocks):
                    break
                block = blocks[block_idx]
                block_no = block.get("block_no", block_idx + 1)
                ep_range = block.get("ep_range", "")
                is_done = block_no in st.session_state.blocks
                is_paywall = block_no in [4, 5]  # 블록 4=EP16~20, 블록 5=EP21~25

                with col:
                    label = f"✓ 블록 {block_no}" if is_done else f"✍️ 블록 {block_no}"
                    badge = " 💰" if is_paywall else ""
                    btn_type = "primary" if not is_done else "secondary"
                    if st.button(f"{label}\n{ep_range}{badge}", key=f"block_{block_no}", use_container_width=True):
                        prev_summary = ""
                        if block_no > 1 and (block_no - 1) in st.session_state.blocks:
                            prev_text = st.session_state.blocks[block_no - 1]
                            prev_summary = prev_text[-300:] if len(prev_text) > 300 else prev_text

                        with st.spinner(f"블록 {block_no} ({ep_range}) 집필 중..."):
                            prompt_text = P.build_block_prompt(
                                st.session_state.concept,
                                block,
                                block_no,
                                prev_summary
                            )
                            result_text = ""
                            placeholder = st.empty()
                            for chunk in call_claude_stream(prompt_text, MAX_TOKENS_BLOCK):
                                result_text += chunk
                                placeholder.text_area(
                                    f"블록 {block_no} 스트리밍...",
                                    result_text,
                                    height=200,
                                    key=f"stream_{block_no}_{len(result_text)}"
                                )
                            st.session_state.blocks[block_no] = result_text
                            st.rerun()

        # 집필된 블록 표시
        if st.session_state.blocks:
            st.markdown("---")
            st.markdown("#### 📝 집필된 대본")

            for block_no in sorted(st.session_state.blocks.keys()):
                block_text = st.session_state.blocks[block_no]
                block_info = blocks[block_no - 1] if block_no <= len(blocks) else {}
                ep_range = block_info.get("ep_range", f"블록 {block_no}")
                phase = block_info.get("phase", "")

                with st.expander(f"블록 {block_no} — {ep_range} [{phase}]", expanded=(block_no == max(st.session_state.blocks.keys()))):
                    # 에피소드별 파싱하여 표시
                    st.text_area(
                        "대본",
                        block_text,
                        height=400,
                        key=f"text_{block_no}"
                    )
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        st.download_button(
                            f"⬇️ 블록 {block_no} TXT",
                            block_text.encode("utf-8"),
                            file_name=f"block{block_no:02d}_{ep_range.replace(' ','')}.txt",
                            mime="text/plain",
                            key=f"dl_block_{block_no}"
                        )
                    with col_d2:
                        if st.button(f"🗑️ 블록 {block_no} 삭제", key=f"del_{block_no}"):
                            del st.session_state.blocks[block_no]
                            st.rerun()

    # ─────────────────────────────────────
    # STEP 4: 다운로드
    # ─────────────────────────────────────
    if st.session_state.blocks:
        st.markdown("---")
        st.markdown('<div class="section-header">STEP 4 &nbsp; 다운로드 <span class="en">DOWNLOAD</span></div>', unsafe_allow_html=True)

        total_blocks = len(st.session_state.blocks)
        total_written = total_blocks * 5
        st.success(f"✅ {total_blocks}개 블록 완성 — 약 {total_written}화 대본")

        # 전체 합치기
        title = st.session_state.concept.get("title", "shortform") if st.session_state.concept else "shortform"

        full_txt = f"👖 BLUE JEANS SHORTFORM ENGINE\n"
        full_txt += f"제목: {title}\n"
        if st.session_state.concept:
            full_txt += f"로그라인: {st.session_state.concept.get('logline','')}\n"
        full_txt += f"생성일: {datetime.now().strftime('%Y-%m-%d')}\n"
        full_txt += "=" * 60 + "\n\n"

        for block_no in sorted(st.session_state.blocks.keys()):
            block_info = st.session_state.arc.get("blocks", [{}])[block_no - 1] if st.session_state.arc else {}
            ep_range = block_info.get("ep_range", f"블록 {block_no}")
            full_txt += f"\n{'='*60}\n[블록 {block_no} — {ep_range}]\n{'='*60}\n\n"
            full_txt += st.session_state.blocks[block_no]
            full_txt += "\n\n"

        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            st.download_button(
                "📄 전체 TXT 다운로드",
                full_txt.encode("utf-8"),
                file_name=f"{title}_전체대본.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col_dl2:
            # CSV (아크 정보)
            if st.session_state.arc:
                csv_lines = ["EP,핵심사건,클리프행어유형,클리프행어내용,감정,과금"]
                for block in st.session_state.arc.get("blocks", []):
                    for ep in block.get("episodes", []):
                        is_pay = "Y" if ep.get("ep", 0) in st.session_state.arc.get("paywall_eps", []) else "N"
                        csv_lines.append(
                            f"EP{ep.get('ep','')},{ep.get('summary','').replace(',','；')},"
                            f"{ep.get('cliffhanger_type','')},{ep.get('cliffhanger','').replace(',','；')},"
                            f"{ep.get('emotion','')},{is_pay}"
                        )
                csv_text = "\n".join(csv_lines)
                st.download_button(
                    "📊 아크 CSV 다운로드",
                    csv_text.encode("utf-8-sig"),
                    file_name=f"{title}_아크.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        with col_dl3:
            if st.button("🔄 전체 초기화", use_container_width=True):
                for k in ["step","concept","arc","blocks","convert_result"]:
                    if k == "step":
                        st.session_state[k] = 0
                    elif k == "blocks":
                        st.session_state[k] = {}
                    else:
                        st.session_state[k] = None
                st.rerun()


# ═══════════════════════════════════════════════════
#  TAB 2: 기존 글 → 숏폼 변환
# ═══════════════════════════════════════════════════

with tab_convert:
    st.markdown("---")
    st.markdown('<div class="section-header">🔄 기존 글 → 숏폼 변환 <span class="en">CONVERT TO SHORTFORM</span></div>', unsafe_allow_html=True)
    st.caption("소설, 시나리오, 웹툰 원작, 실화 등 어떤 텍스트든 막장 숏폼으로 변환합니다.")

    col_cv1, col_cv2 = st.columns([2, 1])
    with col_cv1:
        source_text = st.text_area(
            "원본 텍스트 붙여넣기",
            placeholder="소설 일부, 시나리오, 기사, 줄거리 등 어떤 텍스트든 가능합니다.\n최대 3,000자 분석.",
            height=200
        )
    with col_cv2:
        convert_formula = st.selectbox(
            "변환할 막장 공식",
            list(P.MAKJANG_FORMULAS.keys()),
            format_func=lambda x: P.MAKJANG_FORMULAS[x]["name"],
            key="convert_formula"
        )
        convert_eps = st.selectbox("목표 화수", [20, 30, 50, 100], index=1, key="convert_eps")
        st.markdown(
            f'<div class="callout"><div class="cl">변환 방향</div>'
            f'{P.MAKJANG_FORMULAS[convert_formula]["desc"]}</div>',
            unsafe_allow_html=True
        )

    if st.button("🔄 숏폼으로 변환", type="primary", use_container_width=True, key="btn_convert"):
        if not source_text.strip():
            st.error("원본 텍스트를 입력하세요.")
        else:
            with st.spinner("원본 분석 + 숏폼 변환 중... (30~40초)"):
                prompt_text = P.build_convert_prompt(source_text, convert_formula, convert_eps)
                raw = call_claude(prompt_text, MAX_TOKENS_CONVERT)
                result = safe_json(raw)
                if result:
                    st.session_state.convert_result = result
                    st.rerun()
                else:
                    st.error("변환 실패. 다시 시도하세요.")
                    with st.expander("Raw"):
                        st.text(raw[:2000])

    if st.session_state.convert_result:
        cr = st.session_state.convert_result

        st.markdown("---")

        # 원본 분석
        oa = cr.get("original_analysis", {})
        st.markdown("#### 📖 원본 분석")
        col_oa1, col_oa2 = st.columns(2)
        with col_oa1:
            st.markdown(
                f'<div class="ri"><div class="rl">핵심 갈등</div>{oa.get("core_conflict","")}</div>',
                unsafe_allow_html=True
            )
            if oa.get("usable_elements"):
                elem_html = "".join([f'<div style="font-size:.85rem;margin:.2rem 0">✓ {e}</div>' for e in oa["usable_elements"]])
                st.markdown(f'<div class="ri"><div class="rl">활용 가능한 요소</div>{elem_html}</div>', unsafe_allow_html=True)
        with col_oa2:
            if oa.get("problems"):
                prob_html = "".join([f'<div style="font-size:.85rem;margin:.2rem 0;color:var(--r)">✗ {p}</div>' for p in oa["problems"]])
                st.markdown(f'<div class="ri"><div class="rl">숏폼에 안 맞는 이유</div>{prob_html}</div>', unsafe_allow_html=True)

        # 변환 전략
        cs = cr.get("conversion_strategy", {})
        st.markdown("#### ⚡ 변환 전략")
        col_cs1, col_cs2 = st.columns(2)
        with col_cs1:
            st.markdown(
                f'<div class="card" style="border-left:4px solid var(--y)">'
                f'<div class="cl">주인공 재설계</div>{cs.get("protagonist_rewrite","")}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="card" style="border-left:4px solid var(--r)">'
                f'<div class="cl">악역 주입</div>{cs.get("villain_injection","")}</div>',
                unsafe_allow_html=True
            )
        with col_cs2:
            st.markdown(
                f'<div class="card" style="border-left:4px solid var(--navy)">'
                f'<div class="cl">비밀 설계</div>{cs.get("secret_design","")}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="card" style="border-left:4px solid var(--orange)">'
                f'<div class="cl">막장 비틀기</div>{cs.get("makjang_twist","")}</div>',
                unsafe_allow_html=True
            )

        # 숏폼 컨셉
        sc = cr.get("shortform_concept", {})
        st.markdown("#### 🎬 숏폼 컨셉")
        st.markdown(
            f'<div class="callout"><div class="cl">{sc.get("title","")} — 로그라인</div>'
            f'{sc.get("logline","")}</div>',
            unsafe_allow_html=True
        )
        col_sc1, col_sc2 = st.columns(2)
        with col_sc1:
            st.markdown(
                f'<div class="ri"><div class="rl">EP1 첫 장면</div>{sc.get("hook_ep1","")}</div>',
                unsafe_allow_html=True
            )
        with col_sc2:
            st.markdown(
                f'<div class="ri"><div class="rl">감정 곡선</div>{sc.get("emotional_arc","")}</div>',
                unsafe_allow_html=True
            )

        # 과금 포인트
        st.markdown(
            f'<div class="card" style="border-left:4px solid var(--y);background:#FFFEF0">'
            f'<div class="cl">💰 과금 전환점</div>'
            f'{cs.get("paywall_moment", cr.get("conversion_strategy",{}).get("paywall_moment",""))}'
            f'</div>',
            unsafe_allow_html=True
        )

        # EP 맵
        ep_map = cr.get("episode_map", [])
        if ep_map:
            st.markdown("#### 📊 에피소드 맵")
            ep_html = ""
            for ep in ep_map:
                cliff_color = {
                    "Slap":"#D32F2F","Reveal":"#7B68EE","Reversal":"#FF8C00",
                    "Arrival":"#2EC484","Choice":"#191970","Threat":"#D32F2F","Tears":"#FF69B4"
                }.get(ep.get("cliff_type",""), "#888")
                ep_html += (
                    f'<div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #E6E9EF">'
                    f'<div style="width:100px;font-weight:700;font-size:.85rem;color:var(--navy)">{ep.get("ep_range","")}</div>'
                    f'<div style="flex:1;font-size:.85rem">{ep.get("summary","")}</div>'
                    f'<div style="width:80px;text-align:right;font-size:.8rem;font-weight:700;color:{cliff_color}">{ep.get("cliff_type","")}</div>'
                    f'</div>'
                )
            st.markdown(f'<div class="card">{ep_html}</div>', unsafe_allow_html=True)

        # 파일럿 EP1
        pilot = cr.get("pilot_ep1", "")
        if pilot:
            st.markdown("#### 🎬 파일럿 EP1 대본")
            st.markdown(
                f'<div class="ep-block"><div class="ep-header">EP 1 — 파일럿</div>'
                f'<pre style="white-space:pre-wrap;font-family:var(--body);font-size:.9rem;line-height:1.8">{pilot}</pre>'
                f'</div>',
                unsafe_allow_html=True
            )

            col_dl_cv1, col_dl_cv2 = st.columns(2)
            with col_dl_cv1:
                convert_output = f"BLUE JEANS SHORTFORM ENGINE — 변환 결과\n"
                convert_output += f"제목: {sc.get('title','')}\n로그라인: {sc.get('logline','')}\n\n"
                convert_output += f"[파일럿 EP1]\n{pilot}\n"
                st.download_button(
                    "⬇️ 변환 결과 TXT",
                    convert_output.encode("utf-8"),
                    file_name=f"convert_{sc.get('title','shortform')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with col_dl_cv2:
                if st.button("이 컨셉으로 100화 만들기 →", use_container_width=True, key="convert_to_full"):
                    # 변환 결과를 컨셉으로 이동
                    new_concept = {
                        "title": sc.get("title", ""),
                        "logline": sc.get("logline", ""),
                        "formula": convert_formula,
                        "season_question": sc.get("logline", ""),
                        "protagonist": {"name": "주인공", "age": "", "arc": sc.get("emotional_arc", ""), "identity": "", "secret": "", "dialogue_tone": ""},
                        "villain": {"name": "악역", "age": "", "identity": "", "why_hateful": cs.get("villain_injection",""), "secret": "", "dialogue_tone": ""},
                        "helper": {"name": "", "role": "", "twist": ""},
                        "secrets": [],
                        "paywall_design": {"ep16_reversal": cs.get("paywall_moment",""), "ep20_cliffhanger": ""},
                        "hook_sentence": sc.get("hook_ep1", ""),
                        "total_eps": 100
                    }
                    st.session_state.concept = new_concept
                    st.session_state.step = 1
                    st.success("컨셉이 설정됐습니다. STEP 2 탭에서 아크를 생성하세요.")

st.markdown("---")
st.markdown(
    '<div style="text-align:center;font-size:0.65rem;padding:20px 0;letter-spacing:2px;opacity:0.3;">'
    '© 2026 BLUE JEANS PICTURES · Shortform Engine v1.0 · claude-sonnet-4-6'
    '</div>',
    unsafe_allow_html=True
)
