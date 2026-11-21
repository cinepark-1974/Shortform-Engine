"""
👖 BLUE JEANS SHORTFORM ENGINE v2.8 — main.py
집필: claude-opus-4-6 / 설계: claude-sonnet-4-6
© 2026 BLUE JEANS PICTURES
"""

import math
import streamlit as st
from bj_header import render_header  # 공통 헤더 (Writer Engine 기준)
import anthropic
import json
import re
import io
from datetime import datetime
import importlib
import prompt as P
import doc_import

# 배포 서버가 main.py만 새로 읽고 prompt.py는 예전 것을 메모리에 들고 있을 때가 있다.
# 버전이 맞지 않으면 prompt.py를 다시 읽는다.
EXPECTED_ENGINE_VERSION = "2.8.0"
if getattr(P, "ENGINE_VERSION", None) != EXPECTED_ENGINE_VERSION:
    P = importlib.reload(P)
from docx import Document as DocxDocument
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

MODEL_WRITE = P.MODEL_WRITE   # claude-opus-4-6  — 블록 집필
MODEL_PLAN  = P.MODEL_PLAN    # claude-sonnet-4-6 — 컨셉·아크·변환

MAX_TOKENS_CONCEPT = 6000
MAX_TOKENS_IMPORT  = 4000   # 문서 → 입력칸 채우기
MAX_TOKENS_ARC     = 12000  # 청크당 5블록(25화) — 4회 호출
MAX_TOKENS_BLOCK   = 12000
MAX_TOKENS_CONVERT = 10000
MAX_TOKENS_PILOT   = 8000

# ─── Page Config ──────────────────────────────────
st.set_page_config(
    page_title="BLUE JEANS · Shortform Engine",
    page_icon="👖", layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CSS ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@latest/Paperlogy.css');
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&display=swap');
:root {
    --navy:#191970; --y:#FFCB05; --bg:#F7F7F5; --card:#FFFFFF;
    --border:#E2E2E0; --t:#1A1A2E; --r:#D32F2F; --g:#2EC484;
    --dim:#8E8E99; --lb:#EEEEF6; --orange:#FF6B35; --pink:#FF69B4;
    --body:'Pretendard',-apple-system,sans-serif;
    --head:'Paperlogy','Pretendard',sans-serif;
    --display:'Playfair Display','Paperlogy',serif;
}
html,body,[class*="css"]{font-family:var(--body);color:var(--t);-webkit-font-smoothing:antialiased;}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],
[data-testid="stMainBlockContainer"],[data-testid="stHeader"],[data-testid="stBottom"]{
    background:var(--bg)!important;color:var(--t)!important;}
.stMarkdown,.stText{color:var(--t)!important;}
h1,h2,h3,h4,h5,h6{color:var(--navy)!important;font-family:var(--head)!important;}
section[data-testid="stSidebar"]{display:none;}
.stTextInput input,.stTextArea textarea{
    background:var(--card)!important;color:var(--t)!important;
    border:1.5px solid var(--border)!important;border-radius:8px!important;
    font-family:var(--body)!important;font-size:.9rem!important;padding:.6rem .8rem!important;}
.stTextInput input:focus,.stTextArea textarea:focus{
    border-color:var(--navy)!important;box-shadow:0 0 0 2px rgba(25,25,112,.08)!important;}
.stSelectbox>div>div,[data-baseweb="select"]>div{
    background:var(--card)!important;color:var(--t)!important;
    border-color:var(--border)!important;border-radius:8px!important;}
[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"],[role="option"]{
    background:var(--card)!important;color:var(--t)!important;}
[role="option"]:hover{background:var(--lb)!important;}
.stTextInput label,.stTextArea label,.stSelectbox label{
    color:var(--t)!important;font-weight:600!important;font-size:.82rem!important;}
.stButton>button{
    color:var(--t)!important;border:1.5px solid var(--border)!important;
    background:var(--card)!important;border-radius:8px!important;
    font-family:var(--body)!important;font-weight:600!important;
    font-size:.85rem!important;padding:.5rem 1.2rem!important;transition:all .2s;}
.stButton>button:hover{border-color:var(--navy)!important;box-shadow:0 2px 8px rgba(25,25,112,.08)!important;}
.stButton>button[kind="primary"]{
    background:var(--y)!important;color:var(--navy)!important;
    border-color:var(--y)!important;font-weight:700!important;}
.stButton>button[kind="primary"]:hover{background:#E8B800!important;box-shadow:0 2px 12px rgba(255,203,5,.3)!important;}
[data-testid="stDownloadButton"] button{
    background:var(--navy)!important;color:white!important;
    border-color:var(--navy)!important;font-weight:700!important;}
.stExpander details summary{
    background:var(--card)!important;color:var(--t)!important;
    border:1px solid var(--border)!important;border-radius:8px!important;}
details[open]>div{background:var(--card)!important;}
.stCaption,small{color:var(--dim)!important;}
.stAlert{border-radius:8px!important;}
[data-testid="stVerticalBlock"],[data-testid="stHorizontalBlock"],
[data-testid="stColumn"]{background:transparent!important;}
hr{border-color:var(--border)!important;}

/* ── 브랜딩 ── */
.brand-wrap{text-align:center;padding:1rem 0 0}
.brand-co{font-size:.85rem;font-weight:700;color:var(--navy);letter-spacing:.15em;font-family:var(--head)}
.brand-title{font-size:2.6rem;font-weight:900;color:var(--navy);font-family:var(--display);
    letter-spacing:-.02em;position:relative;display:inline-block}
.brand-title::after{content:'';position:absolute;bottom:2px;left:0;width:100%;height:4px;
    background:var(--y);border-radius:2px}
.brand-sub{font-size:.72rem;font-weight:600;letter-spacing:.18em;color:var(--dim);margin-top:.5rem}

/* ── 노란 섹션 헤더 (Series Engine 통일) ── */
.section-header{background:var(--y);color:var(--navy);padding:.6rem 1rem;border-radius:6px;
    font-weight:800;font-size:1rem;font-family:var(--head);margin:1.5rem 0 .8rem;
    display:flex;justify-content:space-between;align-items:center}
.section-header .en{font-family:var(--display);font-size:.75rem;font-weight:700;
    letter-spacing:.05em;opacity:.7}

/* ── 서브섹션 (하단 선) ── */
.sec{font-size:1.05rem;font-weight:800;color:var(--navy);font-family:var(--head);
     padding:.5rem 0;border-bottom:2px solid var(--y);margin-bottom:1rem}
.en{font-size:.7rem;font-weight:600;color:var(--dim);letter-spacing:.1em;margin-left:.5rem}

/* ── 카드 (Series Engine 통일) ── */
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;
    padding:1.2rem;margin-bottom:.8rem;box-shadow:0 1px 4px rgba(0,0,0,.03);transition:all .2s}
.card:hover{border-color:var(--navy);box-shadow:0 3px 12px rgba(25,25,112,.07);transform:translateY(-1px)}

/* ── 콜아웃 (Series Engine 통일) ── */
.callout{background:var(--lb);border-left:4px solid var(--navy);border-radius:0 8px 8px 0;
    padding:.9rem 1.1rem;margin:.5rem 0;font-size:.88rem}

/* ── 정보 블록 (Series Engine 통일 — 보더 제거, 배경만) ── */
.ri{background:var(--lb);border-radius:8px;padding:.9rem 1rem;margin-bottom:.5rem;
    font-size:.88rem;line-height:1.6}
.rl{color:var(--navy);font-weight:700;font-size:.72rem;letter-spacing:.02em;margin-bottom:.2rem}

/* ── 라벨 ── */
.cl{font-size:.72rem;font-weight:700;color:var(--navy);letter-spacing:.08em;
    text-transform:uppercase;margin-bottom:.3rem}

/* ── 에피소드 블록 ── */
.ep-block{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--orange);
          border-radius:0 12px 12px 0;padding:1.2rem 1.4rem;margin-bottom:1rem}
.ep-hd{font-size:.9rem;font-weight:800;color:var(--orange);letter-spacing:.05em;margin-bottom:.8rem}

/* ── 스텝바 (Series Engine 통일) ── */
.step-bar{display:flex;align-items:center;justify-content:center;margin:1.5rem 0 2rem;gap:0}
.step-dot{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;
          justify-content:center;font-weight:700;font-size:.78rem;border:2px solid transparent;transition:all .2s}
.step-dot.done{background:var(--g);color:white;border-color:var(--g)}
.step-dot.active{background:var(--y);color:var(--navy);border-color:var(--y);box-shadow:0 0 0 4px rgba(255,203,5,.2)}
.step-dot.wait{background:#EDEDF0;color:var(--dim);border-color:#D8D8E0}
.step-line{flex:1;height:2px;background:#D8D8E0;max-width:80px;margin:0 2px}
.step-line.done{background:var(--g)}

/* ── 도파민 배지 ── */
.db{display:inline-block;padding:2px 8px;border-radius:12px;font-size:.68rem;font-weight:800;margin:2px}
.d1{background:#FFE0B2;color:#E65100} .d2{background:#E8F5E9;color:#2E7D32}
.d3{background:#E3F2FD;color:#1565C0} .d4{background:#F3E5F5;color:#6A1B9A}
.d5{background:#FCE4EC;color:#880E4F} .d6{background:#FFF3E0;color:#E65100}
.d7{background:#EFEBE9;color:#4E342E} .d8{background:#E0F7FA;color:#006064}
</style>
""", unsafe_allow_html=True)


# ─── 세션 초기화 ──────────────────────────────────
def init():
    d = {"step":0,"concept":None,"arc":None,"blocks":{},
         "convert_result":None,"block_modes":{},"pilot_text":None,
         "producer_note":"","selected_block":None,
         "premise":"","premise_check":None,"block_checks":{},
         "import_pending":None,"import_report":None,
         "total_eps_key":100,"author_fixed":""}
    for k,v in d.items():
        if k not in st.session_state:
            st.session_state[k] = v
init()


# ─── 유틸리티 ─────────────────────────────────────
def get_client():
    k = st.secrets.get("ANTHROPIC_API_KEY","")
    if not k:
        st.error("ANTHROPIC_API_KEY가 secrets에 없습니다.")
        st.stop()
    return anthropic.Anthropic(api_key=k)

def safe_name(title):
    """긴 문장형 제목을 파일 이름으로 쓸 수 있게 다듬는다."""
    t = re.sub(r'[\\/:*?"<>|…\.]+', "", str(title or "shortform")).strip()
    return (t[:30].strip() or "shortform")


def safe_json(text):
    """Claude 응답에서 JSON을 견고하게 추출한다."""
    if not text: return None
    # 1차: 그대로 파싱
    try: return json.loads(text)
    except: pass
    # 2차: 코드블록 제거
    cleaned = re.sub(r'```json\s*|```\s*', '', text).strip()
    try: return json.loads(cleaned)
    except: pass
    # 3차: 첫 { ~ 마지막 } 범위 추출
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start >= 0 and end > start:
        block = cleaned[start:end+1]
        try: return json.loads(block)
        except: pass
        # 4차: 후행 쉼표 제거
        block = re.sub(r',\s*([}\]])', r'\1', block)
        try: return json.loads(block)
        except: pass
    return None

def call_claude(prompt, max_tokens, model=None, system=None, temperature=None):
    c = get_client()
    kwargs = {
        "model": model or MODEL_PLAN,
        "max_tokens": max_tokens,
        "messages": [{"role":"user","content":prompt}]
    }
    if system:
        kwargs["system"] = system
    if temperature is not None:
        kwargs["temperature"] = temperature
    try:
        r = c.messages.create(**kwargs)
        return "".join(b.text for b in r.content if hasattr(b,"text")).strip()
    except Exception as e:
        st.error(f"API 호출 실패: {type(e).__name__}: {str(e)[:200]}")
        return ""

def call_stream(prompt, max_tokens, model=None):
    c = get_client()
    with c.messages.stream(
        model=model or MODEL_WRITE, max_tokens=max_tokens,
        messages=[{"role":"user","content":prompt}]
    ) as s:
        for t in s.text_stream:
            yield t

def build_docx(text, title="SHORTFORM ENGINE", subtitle=""):
    """숏폼 대본 텍스트를 실제 대본 포맷 DOCX로 변환한다.
    빈줄 규칙: 지문+지문=붙임, 지문↔대사=빈줄, 대사+대사=붙임, 씬 앞=빈줄."""
    doc = DocxDocument()

    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.72)
    section.right_margin = Inches(0.72)

    sn = doc.styles['Normal']
    sn.font.name = '맑은 고딕'
    sn.font.size = Pt(10)
    sn.paragraph_format.space_after = Pt(0)
    sn.paragraph_format.space_before = Pt(0)
    sn.paragraph_format.line_spacing = 1.5

    # 커버 페이지
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before = Pt(120)
    r = p.add_run("시나리오"); r.font.size = Pt(10); r.font.color.rgb = RGBColor(0x8E,0x8E,0x99)
    for _ in range(3): doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title); r.font.size = Pt(24); r.font.bold = True; r.font.color.rgb = RGBColor(0x19,0x19,0x70)
    if subtitle:
        doc.add_paragraph()
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(subtitle); r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x8E,0x8E,0x99)
    for _ in range(6): doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("기획 | 블루진픽처스"); r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x8E,0x8E,0x99)
    doc.add_page_break()

    # 1단계: 줄 분류
    def classify(line):
        t = line.strip()
        if not t: return 'BLANK', t
        if t.startswith('━') or t.startswith('===='): return 'SKIP', t
        if re.match(r'^\[블록\d+', t): return 'BLOCK', t
        if re.match(r'^EP\s*\d+', t) and '|' in t: return 'EP', t
        if t.startswith('[자막]'): return 'SUBTITLE', t
        if re.match(r'^S#\d+', t): return 'SCENE', t
        if re.match(r'^\S+\s*\t+\s*.+$', t) or re.match(r'^\S+\s{2,}.+$', t): return 'DIAL', t
        return 'STGE', t

    classified = [(k, t) for k, t in (classify(l) for l in text.split("\n")) if k != 'SKIP']

    # 2단계: 빈줄 규칙 + 지문 병합
    output = []
    stge_buf = []

    def flush_stge():
        if stge_buf:
            output.append(('STGE', ' '.join(stge_buf)))
            stge_buf.clear()

    for kind, txt in classified:
        prev = output[-1][0] if output else 'BLANK'
        if kind == 'EP':
            flush_stge()
            if prev != 'BLANK': output.append(('BLANK',''))
            output.append((kind, txt))
        elif kind == 'BLOCK':
            flush_stge()
            if prev != 'BLANK': output.append(('BLANK',''))
            output.append((kind, txt))
        elif kind == 'SUBTITLE':
            flush_stge()
            output.append((kind, txt))
        elif kind == 'SCENE':
            flush_stge()
            if prev not in ('BLANK','EP','SUBTITLE'):
                output.append(('BLANK',''))
            output.append((kind, txt))
        elif kind == 'DIAL':
            flush_stge()
            if prev == 'STGE': output.append(('BLANK',''))
            output.append((kind, txt))
        elif kind == 'STGE':
            if prev == 'DIAL' and not stge_buf:
                output.append(('BLANK',''))
            stge_buf.append(txt)
        elif kind == 'BLANK':
            flush_stge()
            if prev != 'BLANK': output.append((kind, txt))
    flush_stge()

    # 공통 텍스트 정리: 대시→쉼표, 이모지 제거, '끊긴다' 제거
    def clean_text(t):
        t = re.sub(r'[\U0001f600-\U0001f9ff\U00002702-\U000027B0\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff✊💢💙💗🥺😡🗡️⚡✨🔥💰]', '', t)
        t = t.replace(' — ', ', ').replace('—', ', ')
        t = re.sub(r',?\s*끊긴다\.?', '', t)  # "끊긴다" "끊긴다." ", 끊긴다"
        t = re.sub(r',\s*,', ',', t)  # 이중 쉼표 제거
        t = re.sub(r',\s*$', '', t)  # 끝에 남은 쉼표 제거
        return t.strip()

    # 3단계: DOCX 생성
    for kind, txt in output:
        if kind == 'BLANK':
            doc.add_paragraph(); continue
        if kind == 'EP':
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn
            # EP 헤더 정리: 이모지 제거, 대시 제거
            clean = re.sub(r'[\U0001f600-\U0001f9ff\U00002702-\U000027B0\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff✊💢💙💗🥺😡🗡️⚡✨🔥💰]', '', txt)
            clean = clean.replace('—', ',').replace(' , ', ', ').strip()
            clean = re.sub(r'\s+', ' ', clean)
            parts = clean.split("|")
            ep_text = parts[0].strip() + " | " + parts[1].strip() if len(parts) >= 2 else clean

            # 1) 상단 구분선
            bp1 = doc.add_paragraph()
            bp1.paragraph_format.space_after = Pt(0)
            pPr1 = bp1._p.get_or_add_pPr()
            pBdr1 = OxmlElement('w:pBdr')
            bot1 = OxmlElement('w:bottom')
            bot1.set(qn('w:val'), 'single'); bot1.set(qn('w:sz'), '4')
            bot1.set(qn('w:space'), '1'); bot1.set(qn('w:color'), '595959')
            pBdr1.append(bot1); pPr1.append(pBdr1)

            # 2) EP 텍스트
            ep_p = doc.add_paragraph()
            ep_p.paragraph_format.space_before = Pt(6)
            ep_p.paragraph_format.space_after = Pt(6)
            r = ep_p.add_run(ep_text); r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = RGBColor(0x59,0x59,0x59)

            # 3) 하단 구분선
            bp2 = doc.add_paragraph()
            bp2.paragraph_format.space_before = Pt(0)
            bp2.paragraph_format.space_after = Pt(6)
            pPr2 = bp2._p.get_or_add_pPr()
            pBdr2 = OxmlElement('w:pBdr')
            top2 = OxmlElement('w:top')
            top2.set(qn('w:val'), 'single'); top2.set(qn('w:sz'), '4')
            top2.set(qn('w:space'), '1'); top2.set(qn('w:color'), '595959')
            pBdr2.append(top2); pPr2.append(pBdr2)
            continue
        p = doc.add_paragraph()
        if kind == 'BLOCK':
            p.paragraph_format.space_before = Pt(24)
            r = p.add_run(txt); r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = RGBColor(0x19,0x19,0x70)
        elif kind == 'SUBTITLE':
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(txt); r.font.size = Pt(10); r.font.bold = True; r.font.color.rgb = RGBColor(0xFF,0x6B,0x35)
        elif kind == 'SCENE':
            p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 2.0
            r = p.add_run(clean_text(txt)); r.font.size = Pt(10); r.font.bold = True
        elif kind == 'DIAL':
            p.paragraph_format.space_after = Pt(2); p.paragraph_format.line_spacing = 2.0
            p.paragraph_format.tab_stops.add_tab_stop(Cm(2.5))
            cleaned = clean_text(txt)
            m = re.match(r'^(\S+)\s*\t+\s*(.+)$', cleaned) or re.match(r'^(\S+)\s{2,}(.+)$', cleaned)
            if m:
                nr = p.add_run(m.group(1)+"\t"); nr.font.size = Pt(10); nr.font.bold = True
                dr = p.add_run(m.group(2)); dr.font.size = Pt(10)
            else:
                r = p.add_run(cleaned); r.font.size = Pt(10)
        elif kind == 'STGE':
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(clean_text(txt)); r.font.size = Pt(10)

    doc.add_paragraph(); doc.add_paragraph()
    ft = doc.add_paragraph(); ft.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = ft.add_run(f"© 2026 BLUE JEANS PICTURES · Shortform Engine v2.8 · {datetime.now().strftime('%Y-%m-%d')}")
    r.font.size = Pt(7); r.font.color.rgb = RGBColor(0xAA,0xAA,0xAA)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


def render_step_bar(step):
    labels = ["컨셉","아크","집필","다운로드"]
    dots = ""
    for i,lbl in enumerate(labels):
        cls = "done" if step>i else ("active" if step==i else "wait")
        sym = "✓" if step>i else str(i+1)
        dots += (f'<div style="display:flex;flex-direction:column;align-items:center;gap:5px">'
                 f'<div class="step-dot {cls}">{sym}</div>'
                 f'<div style="font-size:.68rem;opacity:.65">{lbl}</div></div>')
        if i < 3:
            dots += f'<div class="step-line {"done" if step>i else ""}"></div>'
    st.markdown(f'<div class="step-bar">{dots}</div>', unsafe_allow_html=True)

def d_badge(d_str):
    names = {"D1":"간헐적강화","D2":"지위역전","D3":"정체드러남","D4":"예측오류",
             "D5":"위험설렘","D6":"밀당","D7":"대리복수","D8":"체크리스트"}
    colors = {"D1":"d1","D2":"d2","D3":"d3","D4":"d4","D5":"d5","D6":"d6","D7":"d7","D8":"d8"}
    r = ""
    for d in ["D1","D2","D3","D4","D5","D6","D7","D8"]:
        if d in str(d_str):
            r += f'<span class="db {colors[d]}">{names[d]}</span>'
    return r or f'<span class="db d8">{d_str}</span>'

CAT_COLOR = {
    "怒 분노계":"#D32F2F","哀 슬픔계":"#7B68EE","喜 기쁨계":"#FF69B4",
    "樂 쾌감계":"#2EC484","張 긴장계":"#FF8C00"
}


def arc_ledger(blocks, before_ep=None):
    """아크에서 이미 일어난 일을 'EP n: 사건' 한 줄씩으로 모은다. 같은 사건을 되풀이하지 않게 하는 장부."""
    lines = []
    for b in blocks or []:
        for e in b.get("episodes", []):
            try:
                n = int(e.get("ep", 0))
            except (TypeError, ValueError):
                continue
            if before_ep is not None and n >= before_ep:
                continue
            ev = str(e.get("summary", "")).strip()
            if ev:
                lines.append(f"EP{n}: {ev}")
    return "\n".join(lines)


def generate_arc_chunks(concept, total_eps, producer_note, progress_placeholder):
    """25화씩 청크 호출로 아크를 생성하고 병합한다. 총 화수 20~100. 실패 시 1회 자동 재시도."""
    total_chunks = math.ceil(int(total_eps) / 25)
    all_blocks = []
    all_milestones = []
    all_summaries = []
    arc_issues_all = []
    prev_summary = ""
    subtitle_style = st.session_state.get("subtitle_key", P.DEFAULT_SUBTITLE)
    lead = st.session_state.get("lead_key", P.DEFAULT_LEAD)
    paywall_ep = int(st.session_state.get("paywall_key", P.DEFAULT_PAYWALL))
    target = st.session_state.get("target_key", P.DEFAULT_TARGET)
    ai_mode = bool(st.session_state.get("ai_mode_key", False))
    premise = st.session_state.get("premise", "")
    sub_max = P.SUBTITLE_STYLES[subtitle_style]["max_chars"]
    sub_limit = f"MAX {sub_max} chars Korean" if sub_max else "empty string"

    for chunk in range(1, total_chunks + 1):
        start_ep = (chunk - 1) * 25 + 1
        end_ep = min(chunk * 25, total_eps)

        result = None
        raw = ""
        best, best_issues = None, None
        fix_note = ""
        prior_phases = [str(b.get("phase", "")) for b in all_blocks]
        for attempt in range(3):  # 파싱 실패 재시도 1회 + 점검 불합격 재설계 1회
            label = "다시 설계 중" if fix_note else "생성 중"
            with st.spinner(f"🔄 아크 청크 {chunk}/{total_chunks} {label}... (EP{start_ep}~{end_ep})"):
                raw = call_claude(
                    P.build_arc_prompt(concept, total_eps,
                        producer_note=(producer_note + "\n\n" + fix_note).strip() if fix_note else producer_note,
                        chunk=chunk, total_chunks=total_chunks,
                        prev_summary=prev_summary,
                        subtitle_style=subtitle_style,
                        lead=lead, paywall_ep=paywall_ep,
                        target=target, ai_mode=ai_mode, premise=premise),
                    MAX_TOKENS_ARC,
                    system=f"You are a concise JSON generator for a {int(total_eps)}-episode drama arc. Rules: 1) Output ONLY valid JSON. 2) No markdown fences, no explanation. 3) summary: MAX 15 chars Korean. 4) cliffhanger: MAX 15 chars Korean. 5) first_subtitle: {sub_limit}. 6) Do NOT add fields not in the schema (no dopamine_moment, no market_hook, no recommended_emotion_modes). 7) Complete ALL {(end_ep - start_ep + 1) // 5} blocks of this chunk with ALL 5 episodes each. Never truncate."
                )
            cand = safe_json(raw)
            if not cand or not cand.get("blocks"):
                if best is not None:
                    break
                progress_placeholder.warning(f"청크 {chunk} 파싱 실패 — 자동 재시도 중...")
                continue
            issues = P.check_arc_chunk(cand["blocks"], prior_phases)
            if best is None or len(issues) < len(best_issues):
                best, best_issues = cand, issues
            if not issues or fix_note:
                break
            fix_note = P.build_arc_fix_note(issues)
            progress_placeholder.warning(f"청크 {chunk}: 되풀이·규칙 용어 {len(issues)}건 — 다시 설계합니다.")
        result = best
        if result is not None:
            arc_issues_all.extend(best_issues or [])

        if not result or not result.get("blocks"):
            st.error(f"청크 {chunk} 생성 실패 (2회 시도).")
            with st.expander(f"🔍 청크 {chunk} Raw 응답 (디버깅용)", expanded=True):
                st.code(raw[:3000] if raw else "(빈 응답 — API 호출 자체가 실패했을 수 있습니다)")
            return None

        all_blocks.extend(result.get("blocks", []))
        all_milestones.extend(result.get("dopamine_milestones", []))
        chunk_summary = result.get("chunk_summary", "")
        all_summaries.append(f"[EP{start_ep}~{end_ep}] {chunk_summary}")
        prev_summary = ("\n".join(all_summaries)
                        + "\n\n[이미 쓴 블록 국면 이름 — 겹치지 않게]\n"
                        + ", ".join(str(b.get("phase", "")) for b in all_blocks)
                        + "\n\n[이미 일어난 일 — 화별]\n" + arc_ledger(all_blocks))
        progress_placeholder.success(f"✅ 청크 {chunk}/{total_chunks} 완료 — {len(result.get('blocks',[]))}블록")

    # 병합
    merged = {
        "arc_summary": " → ".join(all_summaries),
        "dopamine_milestones": all_milestones,
        "blocks": all_blocks,
        "paywall_eps": list(range(paywall_ep, paywall_ep + 5)),
        "check_issues": arc_issues_all,
    }
    progress_placeholder.success(
        f"✅ 아크 생성 완료 — {len(all_blocks)}블록 · {len(all_milestones)}개 도파민 마일스톤"
        + (f" · 점검에 남은 것 {len(arc_issues_all)}건" if arc_issues_all else " · 되풀이 점검 통과"))
    return merged


def highlight_script(text):
    """숏폼 대본 텍스트를 지문/대사/자막/헤더별 색상 하이라이팅 HTML로 변환."""
    import html as html_mod
    lines = text.split("\n")
    out = []
    for line in lines:
        raw = line.rstrip()
        escaped = html_mod.escape(raw)

        # 빈 줄
        if not raw.strip():
            out.append('<div style="height:.5rem"></div>')
            continue

        # EP 헤더 (━━━ 또는 EP 숫자 |)
        if raw.startswith("━") or (re.match(r'^EP\s*\d+', raw) and "|" in raw):
            out.append(
                f'<div style="font-weight:900;font-size:.88rem;color:var(--navy);'
                f'background:var(--lb);padding:6px 10px;border-radius:6px;margin:1rem 0 .4rem;'
                f'border-left:4px solid var(--y);letter-spacing:.03em">{escaped}</div>'
            )
            continue

        # [자막] 태그
        if raw.strip().startswith("[자막]"):
            out.append(
                f'<div style="font-weight:800;font-size:.85rem;color:#E65100;'
                f'background:#FFF3E0;padding:5px 10px;border-radius:6px;margin:.3rem 0;'
                f'border-left:4px solid var(--orange)">{escaped}</div>'
            )
            continue

        # S# 씬 헤더 (S#1. 장소. 낮/밤.)
        if re.match(r'^S#\d+', raw):
            out.append(
                f'<div style="font-weight:800;font-size:.82rem;color:var(--navy);'
                f'background:var(--lb);padding:5px 10px;border-radius:6px;margin:.6rem 0 .2rem;'
                f'border-left:4px solid var(--navy)">{escaped}</div>'
            )
            continue

        # 장소 헤더 (XX. 낮/밤/저녁/새벽.)
        if re.match(r'^.+\.\s*(낮|밤|저녁|새벽|아침|오후|오전|심야)', raw):
            out.append(
                f'<div style="font-weight:700;font-size:.82rem;color:var(--dim);'
                f'padding:3px 10px;border-bottom:1px solid var(--border);margin:.4rem 0 .2rem;'
                f'letter-spacing:.05em">{escaped}</div>'
            )
            continue

        # 대사 (인물명  대사 — 두 칸 이상 공백)
        m = re.match(r'^(\S+)\s{2,}(.+)$', raw)
        if m:
            name = html_mod.escape(m.group(1))
            dialogue = html_mod.escape(m.group(2))
            out.append(
                f'<div style="padding:3px 10px;margin:.15rem 0;line-height:1.8">'
                f'<span style="font-weight:800;font-size:.82rem;color:var(--navy);'
                f'min-width:50px;display:inline-block">{name}</span>'
                f'<span style="font-size:.88rem;color:var(--t);margin-left:.3rem">{dialogue}</span>'
                f'</div>'
            )
            continue

        # 지문 (나머지)
        out.append(
            f'<div style="font-size:.85rem;color:#555;padding:2px 10px;margin:.1rem 0;'
            f'line-height:1.8;font-style:italic">{escaped}</div>'
        )

    return (
        '<div class="card" style="padding:1rem 0;border-left:4px solid var(--orange);'
        'overflow-y:auto;max-height:600px">' + "\n".join(out) + '</div>'
    )


# ─── 브랜드 헤더 ──────────────────────────────────
render_header("SHORTFORM ENGINE", tagline="100 EPISODES × 1 MINUTE", note="v2.8 · DOPAMINE DESIGN · 25 EMOTIONS · 100EP")
st.caption(f"집필: {MODEL_WRITE} · 설계: {MODEL_PLAN} · 22클릭 → 100화 완성")

# ─── 프로듀서 노트 (전 단계 공통) ─────────────────
with st.expander("🎬 프로듀서 노트 — 모든 단계에 반영됩니다", expanded=bool(st.session_state.producer_note)):
    st.markdown(
        '<div style="font-size:.75rem;color:var(--dim);margin-bottom:.5rem">'
        '파일럿을 보고 느낀 키워드, 톤 지시, 강조할 설정 등을 적어주세요.<br>'
        '여기에 쓴 내용은 컨셉 설정 · 아크 생성 · 블록 집필 · 파일럿 집필에 모두 주입됩니다.'
        '</div>', unsafe_allow_html=True
    )
    pn = st.text_area("프로듀서 노트",
        value=st.session_state.producer_note,
        placeholder="예: 대사를 더 건조하게. 로맨스 비중 낮추고 복수 중심.\n예: '통장 잔고 1,200원' 같은 구체적 숫자 많이 쓸 것.\n예: 클리프행어에 소리 연출(발소리, 벨소리) 적극 활용.",
        height=80, label_visibility="collapsed", key="pn_input")
    if pn != st.session_state.producer_note:
        st.session_state.producer_note = pn

# ─── 공통 설정 (전 단계 공통) ────────────────────
# 컨셉을 만들기 전에 고릅니다. 중간에 바꾸면 이미 만든 컨셉·아크와 어긋납니다.
col_tone, col_lead, col_sub = st.columns(3)
with col_tone:
    tone_key = st.selectbox(
        "작품 톤", list(P.TONE_RULES.keys()),
        index=list(P.TONE_RULES.keys()).index(P.DEFAULT_TONE),
        format_func=lambda x: P.TONE_RULES[x]["name"], key="tone_key")
    st.caption(P.TONE_RULES[tone_key]["desc"])
with col_lead:
    lead_key = st.selectbox(
        "주인공 향", list(P.LEAD_RULES.keys()),
        index=list(P.LEAD_RULES.keys()).index(P.DEFAULT_LEAD),
        format_func=lambda x: P.LEAD_RULES[x]["name"], key="lead_key")
    st.caption(P.LEAD_RULES[lead_key]["desc"])
with col_sub:
    subtitle_key = st.selectbox(
        "첫 자막 형식", list(P.SUBTITLE_STYLES.keys()),
        index=list(P.SUBTITLE_STYLES.keys()).index(P.DEFAULT_SUBTITLE),
        format_func=lambda x: P.SUBTITLE_STYLES[x]["name"], key="subtitle_key")
    st.caption(P.SUBTITLE_STYLES[subtitle_key]["desc"])

col_pay, col_target, col_ai = st.columns(3)
with col_pay:
    paywall_key = int(st.number_input(
        "첫 과금 관문 (화)", min_value=P.PAYWALL_MIN, max_value=P.PAYWALL_MAX,
        value=P.DEFAULT_PAYWALL, step=1, key="paywall_key"))
    st.caption(f"무료로 보여 주는 마지막 화입니다. EP {paywall_key}의 끝에서 끊고 EP {paywall_key + 1}부터 결제. 무료 5화형이면 5.")
with col_target:
    target_key = st.text_input("타겟", value=P.DEFAULT_TARGET, key="target_key")
    st.caption("주인공의 나이와 처지를 이 타겟에 맞춥니다.")
with col_ai:
    ai_mode_key = st.toggle("AI 제작 모드", value=False, key="ai_mode_key")
    st.caption("얼굴 4명·세트 5곳 이하, 몸싸움은 소리와 암전, 침대 2인 금지, 식탁·클로즈업·손·소품 위주.")
    auto_check_key = st.toggle("집필 후 자동 점검", value=True, key="auto_check_key")
    st.caption("대사 0줄·혼자 씬 10% 초과·화면 인서트 1/3 초과면 다시 씁니다.")


# ─── 문서에서 가져오기 (v2.5) ─────────────────────
# 입력칸 이름 → 화면 위젯 키
IMPORT_WIDGET_KEYS = {
    "premise": "premise_input",
    "protagonist": "protagonist_input",
    "villain": "villain_input",
    "secrets": "secrets_input",
    "season_question": "sq_input",
    "supporting_hint": "hint_input",
    "custom_idea": "custom_input",
}
TOTAL_EPS_OPTIONS = [20, 30, 50, 80, 90, 100]


def current_concept_fields():
    """지금 입력칸에 적혀 있는 글을 모은다."""
    return {f: (st.session_state.get(k) or "").strip()
            for f, k in IMPORT_WIDGET_KEYS.items()}


def _as_text(v):
    """AI가 줄 목록으로 돌려줘도 입력칸에 넣을 수 있게 글로 바꾼다."""
    if isinstance(v, list):
        return "\n".join(str(x).strip() for x in v if str(x).strip())
    if isinstance(v, dict):
        return "\n".join(f"{k}: {x}" for k, x in v.items())
    return str(v or "").strip()


def run_field_fill(doc_text, source_label, fill_missing=True, overwrite=False):
    """문서(없으면 이미 적힌 칸)를 읽혀 입력칸을 채운다. 성공하면 True."""
    cur = current_concept_fields()
    keep = {} if overwrite else {f: v for f, v in cur.items() if v}
    raw = call_claude(
        P.build_import_prompt(doc_text, keep, fill_missing,
                              total_eps=st.session_state.get("total_eps_key", 100),
                              target=st.session_state.get("target_key", "")),
        MAX_TOKENS_IMPORT)
    res = safe_json(raw)
    if not res or not isinstance(res.get("fields"), dict):
        st.error("문서를 입력칸으로 나누지 못했습니다. 다시 시도해 주세요.")
        if raw:
            with st.expander("Raw"): st.text(raw[:1000])
        return False

    pending, filled_doc, filled_ai, kept, empty = {}, [], [], [], []
    generated = set(res.get("generated") or [])
    for f, wkey in IMPORT_WIDGET_KEYS.items():
        if f in keep:
            kept.append(f)
            continue
        val = _as_text(res["fields"].get(f))
        if not val:
            empty.append(f)
            continue
        pending[wkey] = val
        (filled_ai if f in generated else filled_doc).append(f)

    fk = res.get("formula_key")
    if fk in P.MAKJANG_FORMULAS:
        pending["fs"] = fk
    try:
        eps = int(res.get("total_eps") or 0)
    except (TypeError, ValueError):
        eps = 0
    if eps in TOTAL_EPS_OPTIONS:
        pending["total_eps_key"] = eps

    st.session_state.import_pending = pending
    st.session_state.import_report = {
        "source": source_label, "title": _as_text(res.get("title")),
        "from_doc": filled_doc, "generated": filled_ai, "kept": kept, "empty": empty,
        "formula_key": fk if fk in P.MAKJANG_FORMULAS else "",
        "formula_reason": _as_text(res.get("formula_reason")),
        "total_eps": eps if eps in TOTAL_EPS_OPTIONS else 0,
        "doc_eps": eps,
        "warning": _as_text(res.get("warning")),
    }
    st.session_state.premise_check = None   # 전제가 바뀌었으니 점검도 다시
    return True


def apply_import_pending():
    """입력칸 위젯이 그려지기 전에, 가져온 값을 위젯에 넣는다."""
    pending = st.session_state.import_pending
    if pending:
        for k, v in pending.items():
            st.session_state[k] = v
        st.session_state.import_pending = None


def show_import_report():
    rp = st.session_state.import_report
    if not rp:
        return
    name = lambda keys: ", ".join(P.IMPORT_FIELDS[k] for k in keys)
    lines = []
    if rp["from_doc"]:
        lines.append(f'<div>📄 <b>문서에서 가져온 칸</b>: {name(rp["from_doc"])}</div>')
    if rp["generated"]:
        lines.append(f'<div style="color:var(--orange)">✨ <b>AI가 지어서 채운 칸</b> (읽고 고쳐 주세요): {name(rp["generated"])}</div>')
    if rp["kept"]:
        lines.append(f'<div>✍️ <b>이미 적혀 있어 그대로 둔 칸</b>: {name(rp["kept"])}</div>')
    if rp["empty"]:
        lines.append(f'<div style="color:var(--dim)">⬜ <b>비어 있는 칸</b>: {name(rp["empty"])}</div>')
    if rp["formula_key"]:
        lines.append(f'<div>🧭 <b>막장 공식</b>: {P.MAKJANG_FORMULAS[rp["formula_key"]]["name"]} — {rp["formula_reason"]}</div>')
    if rp["total_eps"]:
        lines.append(f'<div>🎞 <b>총 에피소드</b>: 문서에 적힌 {rp["total_eps"]}화로 맞췄습니다.</div>')
    elif rp["doc_eps"]:
        lines.append(f'<div style="color:var(--dim)">🎞 문서에는 {rp["doc_eps"]}화로 적혀 있습니다. 이 엔진의 화수 선택지에 없어 그대로 두었습니다.</div>')
    if rp["warning"]:
        lines.append(f'<div style="color:#D32F2F">⚠ {rp["warning"]}</div>')
    title = f' — {rp["title"]}' if rp["title"] else ""
    st.markdown(
        f'<div class="callout"><div class="cl">가져오기 결과 · {rp["source"]}{title}</div>'
        f'<div style="font-size:.82rem;line-height:1.9">{"".join(lines)}</div></div>',
        unsafe_allow_html=True)


def run_premise_check(premise):
    """한 문장 전제에 바닥·뒤집는 장치·약속된 쾌감이 있는지 점검해 세션에 담는다."""
    raw = call_claude(P.build_premise_check_prompt(premise), 1200, temperature=0)
    res = safe_json(raw) or {}
    st.session_state.premise_check = {"premise": premise, "result": res}
    return res


def show_premise_check():
    """마지막 전제 점검 결과를 화면에 보여 준다."""
    pc = st.session_state.get("premise_check")
    if not pc or not pc.get("result"):
        return
    r = pc["result"]
    rows = [("바닥", r.get("floor")), ("뒤집는 장치", r.get("device")), ("약속된 쾌감", r.get("promise"))]
    body = "".join(
        f'<div style="font-size:.82rem;margin:.15rem 0">{"✅" if v else "❌"} <b>{k}</b> — {v or "전제에 없음"}</div>'
        for k, v in rows)
    st.markdown(f'<div class="callout"><div class="cl">전제 점검</div>{body}</div>', unsafe_allow_html=True)
    if not r.get("pass"):
        if r.get("advice"):
            st.warning(r["advice"])
        if r.get("rewrite"):
            st.info(f"고쳐 쓴 예: {r['rewrite']}")


def stream_block(prompt, label, key_prefix):
    """블록 대본을 스트리밍으로 받아 온다."""
    rt = ""
    ph = st.empty()
    for chunk in call_stream(prompt, MAX_TOKENS_BLOCK, model=MODEL_WRITE):
        rt += chunk
        if len(rt) % 200 < 10:
            ph.text_area(label, rt, height=200, key=f"{key_prefix}_{len(rt)}")
    ph.empty()
    return rt


def write_block_checked(make_prompt, concept, bn):
    """블록을 쓰고 자동 점검한다. 걸리면 최대 2번 다시 쓴다.
    make_prompt(rewrite_note) -> 프롬프트 문자열. 돌려주는 값: (대본, 점검 결과)"""
    rt = stream_block(make_prompt(""), f"블록{bn} 집필 중...", f"s_{bn}_0")
    check = P.check_script(rt, concept, ai_mode=ai_mode_key)
    tries = 0
    while auto_check_key and not check["ok"] and tries < 2:
        tries += 1
        st.warning(f"자동 점검 불합격 — 다시 씁니다 ({tries}/2)\n\n" + "\n".join(f"- {i}" for i in check["issues"][:6]))
        rt2 = stream_block(make_prompt(P.build_rewrite_note(check["issues"], rt)),
                           f"블록{bn} 다시 쓰는 중... ({tries}/2)", f"s_{bn}_{tries}")
        check2 = P.check_script(rt2, concept, ai_mode=ai_mode_key)
        if len(check2["issues"]) <= len(check["issues"]):   # 더 나은 쪽을 남긴다
            rt, check = rt2, check2
    check["rewrites"] = tries
    return rt, check


def show_block_check(bn):
    """블록의 자동 점검 결과를 보여 준다."""
    ck = st.session_state.block_checks.get(bn)
    if not ck:
        return
    stt = ck.get("stats", {})
    line = (f"씬 {stt.get('scenes', 0)}개 중 혼자 씬 {stt.get('solo_scenes', 0)}개 · "
            + " · ".join(f"EP{e['ep']} 대사 {e['dialogue']}줄" for e in stt.get("per_ep", [])))
    if ck.get("ok"):
        st.success(f"자동 점검 통과 (다시 쓴 횟수 {ck.get('rewrites', 0)}) — {line}")
    else:
        st.warning(f"자동 점검에서 남은 문제 (다시 쓴 횟수 {ck.get('rewrites', 0)}) — {line}\n\n"
                   + "\n".join(f"- {i}" for i in ck.get("issues", [])))


def common_opts():
    """모든 프롬프트 빌더에 함께 넘기는 공통 설정."""
    return dict(tone=tone_key, subtitle_style=subtitle_key, lead=lead_key,
                paywall_ep=paywall_key, target=target_key, ai_mode=ai_mode_key)


def block_has_paywall(bn):
    """이 블록(5화)에 과금 구간의 화가 들어 있는가."""
    pw_eps = (st.session_state.arc or {}).get("paywall_eps", list(range(paywall_key, paywall_key + 5)))
    return any((bn - 1) * 5 < e <= bn * 5 for e in pw_eps)


# 로맨스 축이 없는 작품에서 로맨스 감정 모드를 바꿔 끼울 짝
NO_ROMANCE_SWAP = {"유혹": "긴장", "스윗": "연민", "설렘": "짜릿",
                   "질투": "경멸", "미련": "배신감", "그리움": "상실"}


def has_no_romance():
    """컨셉에 로맨스 축이 없다고 적혀 있는지 본다."""
    c = st.session_state.concept or {}
    ld = c.get("location_design")
    peak = str(ld.get("romance_peak", "")) if isinstance(ld, dict) else ""
    text = peak + " " + (st.session_state.author_fixed or "") + " " + (st.session_state.premise or "")
    return any(k in text for k in ("로맨스 없음", "로맨스 축 없음", "해당 없음", "로맨스는 없"))


def default_block_modes(bn, blk):
    """블록의 기본 감정 모드 5개. 직접 고른 것 > 아크가 화마다 정한 감정 > 기본 콤보 순.

    아크가 정한 감정이 몇 화만 비어 있거나 목록에 없는 말이면, 그 화만 기본 콤보로 메운다.
    """
    chosen = st.session_state.block_modes.get(bn)
    if chosen:
        return chosen
    no_rom = has_no_romance()
    total_blocks = max(1, len((st.session_state.arc or {}).get("blocks", [])) or 20)
    pos = bn / total_blocks
    if block_has_paywall(bn): combo = P.EMOTIONAL_MODE_COMBOS["과금_전환"]
    elif pos <= 0.2: combo = P.EMOTIONAL_MODE_COMBOS["분노_축적"]
    elif pos <= 0.55: combo = P.EMOTIONAL_MODE_COMBOS["감정_시소"]
    elif pos <= 0.85: combo = P.EMOTIONAL_MODE_COMBOS["복수_시작" if no_rom else "로맨스_피크"]
    else: combo = P.EMOTIONAL_MODE_COMBOS["클라이맥스"]
    arc_modes = [e.get("emotion_mode", "") for e in blk.get("episodes", [])]
    modes = []
    for i in range(5):
        m = arc_modes[i] if i < len(arc_modes) else ""
        modes.append(m if m in P.EMOTIONAL_MODES else combo[i])
    if no_rom:
        modes = [NO_ROMANCE_SWAP.get(m, m) for m in modes]
    return modes


def note_with_fixed():
    """프로듀서 노트 + 작가가 커스텀 아이디어에 정해 둔 것. 아크와 집필에 그대로 넘긴다."""
    note = st.session_state.producer_note or ""
    fixed = (st.session_state.author_fixed or "").strip()
    if fixed:
        note = (note + "\n\n" if note else "") + (
            "[작가가 정해 둔 것 — 반드시 지킨다]\n"
            "따옴표 안의 대사는 글자 그대로 쓴다. 'EP1 엔딩'처럼 자리가 적힌 것은 그 자리에 넣는다.\n"
            "'엔딩 대사'로 정해 둔 것은 그 화의 마지막 대사다. 그 뒤에 대사나 씬을 더 붙이지 않는다.\n"
            + fixed)
    return note


def china_tone_notice(market):
    """중국 시장 + 독한 톤 조합일 때 안내를 띄운다."""
    if market == "중국" and tone_key == "harsh":
        st.warning("중국 유통에서는 학대·가정폭력 장면이 단속 대상이라는 보도가 있습니다. "
                   "독한 톤의 손찌검·무릎 장면이 심의에 걸릴 수 있습니다. 중국 유통이 목표라면 조용한 톤을 권합니다.")

tab_create, tab_convert = st.tabs(["✍️ 새 숏폼 만들기", "🔄 기존 글 → 숏폼 변환"])


# ═══════════════════════════════════════════════════
#  TAB 1: 새 숏폼 만들기
# ═══════════════════════════════════════════════════
with tab_create:
    render_step_bar(st.session_state.step)
    st.markdown('<hr>', unsafe_allow_html=True)

    # ── STEP 1: 컨셉 ──────────────────────────────
    st.markdown('<div class="section-header">📝 컨셉 설정 <span class="en">STEP 1 · CONCEPT</span></div>', unsafe_allow_html=True)

    apply_import_pending()

    with st.expander("📎 문서에서 가져오기 — 기획서·시놉시스를 올리면 아래 칸을 자동으로 채웁니다",
                     expanded=not any(current_concept_fields().values())):
        col_up, col_paste = st.columns(2)
        with col_up:
            up = st.file_uploader(
                "파일 올리기", type=doc_import.SUPPORTED, key="import_file",
                help="PDF · 워드(DOCX) · 한글(HWP/HWPX) · TXT · MD · JSON")
        with col_paste:
            pasted = st.text_area(
                "또는 글 붙여넣기", height=110, key="import_paste",
                placeholder="다른 곳에서 쓴 기획서, 시놉시스, 줄거리, 인물 소개를 그대로 붙여넣으세요.")
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            imp_fill = st.checkbox("문서에 없는 칸은 AI가 지어서 채우기", value=True, key="import_fill")
        with col_o2:
            imp_over = st.checkbox("이미 적은 칸도 문서 내용으로 덮어쓰기", value=False, key="import_over")
        if st.button("📥 문서 읽고 칸 채우기", use_container_width=True, key="import_btn"):
            doc_text, label = "", ""
            if up is not None:
                try:
                    got = doc_import.extract_text(up.name, up.getvalue())
                    doc_text, label = got["text"], up.name
                    if got["trimmed"]:
                        st.info(f"문서가 깁니다({got['chars']:,}자). 앞부분과 끝부분 {doc_import.MAX_CHARS:,}자만 읽습니다.")
                except doc_import.DocImportError as e:
                    st.error(str(e))
            elif pasted.strip():
                doc_text, _ = doc_import.trim_for_ai(pasted.strip())
                label = "붙여넣은 글"
            else:
                st.error("파일을 올리거나 글을 붙여넣어 주세요.")
            if doc_text:
                with st.spinner("문서를 읽고 칸을 나누는 중... (20~40초)"):
                    if run_field_fill(doc_text, label, fill_missing=imp_fill, overwrite=imp_over):
                        st.rerun()
    show_import_report()

    premise = st.text_area(
        "한 문장 전제",
        placeholder="바닥, 뒤집는 장치, 약속된 쾌감이 한 문장(길어도 세 문장)에 들어가야 합니다.\n"
                    "예: 가진 것 없이 쫓겨난 며느리가(바닥) 죽기 전날로 돌아와(뒤집는 장치) 자신을 죽인 사람 대신 그 집의 전 재산을 차지한다(약속된 쾌감).",
        height=80, key="premise_input")
    st.session_state.premise = premise
    col_pc1, col_pc2 = st.columns([1, 3])
    with col_pc1:
        if st.button("🔎 전제 점검", use_container_width=True):
            if premise.strip():
                with st.spinner("전제 점검 중..."):
                    run_premise_check(premise)
            else:
                st.error("전제를 먼저 입력하세요.")
    with col_pc2:
        skip_premise = st.checkbox("전제 점검에 걸려도 그대로 컨셉 생성", value=False, key="skip_premise")
    if (st.session_state.premise_check or {}).get("premise") == premise:
        show_premise_check()

    formula_options = {
        "재벌복수":"👑 재벌 복수 — 신분격차+출생비밀+지위역전",
        "능력각성":"⚡ 능력 각성 — 1화 능력 발현+숨긴 정체",
        "귀환재회":"🔄 귀환/재회 — 5년 후 돌아온 사람+아이의 정체",
        "복수극":  "🗡️ 복수극 — 배신→하나씩 무너뜨리기",
        "섬혼":    "💍 번개 결혼 — 당일 파혼+처음 본 남자+남편의 숨긴 정체",
        "이혼후회":"📄 이혼 후 후회남 — 도장 찍고 떠난 아내+뒤늦게 매달리는 남편",
        "감성숏폼":"💕 감성 숏폼 — 설렘+배신+눈물 (원작 변환형)",
    }

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        formula_key = st.selectbox("막장 공식", list(formula_options.keys()),
                                    format_func=lambda x:formula_options[x], key="fs")
        formula = P.MAKJANG_FORMULAS[formula_key]
        st.markdown(
            f'<div class="callout"><div class="cl">공식 설명</div>{formula["desc"]}<br>'
            f'<span style="font-size:.8rem;color:var(--navy);font-weight:700">💰 과금:</span>'
            f'<span style="font-size:.8rem"> {P.fill_paywall(formula["paywall"], paywall_key)}</span><br>'
            f'<span style="font-size:.75rem;color:var(--orange)">🧠 도파민: {formula["dopamine_key"][:60]}...</span>'
            f'</div>', unsafe_allow_html=True
        )

    with col_f2:
        col_m, col_r = st.columns(2)
        with col_m:
            market = st.selectbox("타겟 시장", ["한국","글로벌","중국"], key="mkt")
        china_tone_notice(market)
        with col_r:
            rating = st.selectbox("수위 등급",
                ["family","teen","adult"],
                format_func=lambda x:{"family":"👨‍👩‍👧 전체가","teen":"🔞 15세+","adult":"🔞 19+"}[x],
                index=1, key="rtg")
        total_eps = st.selectbox("총 에피소드", TOTAL_EPS_OPTIONS, key="total_eps_key")

        rating_info = P.CONTENT_RATING_RULES[rating]
        st.markdown(
            f'<div class="ri" style="border-left:3px solid var(--orange)">'
            f'<div class="rl" style="color:var(--orange)">🧠 도파민 연출</div>'
            f'<div style="font-size:.75rem">{rating_info["dopamine_note"][:80]}...</div>'
            f'</div>', unsafe_allow_html=True
        )
        if market in ["중국","글로벌"]:
            st.markdown(
                f'<div class="ri" style="border-left:3px solid #D32F2F">'
                f'<div class="rl" style="color:#D32F2F">🌐 Global Strategy</div>'
                f'<div style="font-size:.75rem">{formula.get("global_variant","")[:80]}...</div>'
                f'</div>', unsafe_allow_html=True
            )

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        protagonist = st.text_area("주인공 설정",
            placeholder="이름/나이/직업\n처한 상황 (최대한 불쌍하게 — 낙차가 클수록 역전의 도파민이 크다)\n숨겨진 능력/정체/비밀 (역전의 씨앗)",
            height=100, key="protagonist_input")
        secrets = st.text_area("핵심 비밀 2~3개",
            placeholder="비밀1: EP__에서 드러남 — 내용\n비밀2: EP__에서 드러남 — 내용\n비밀3: EP__에서 드러남 — 내용",
            height=80, key="secrets_input")
    with col_i2:
        villain = st.text_area("메인 악역 설정",
            placeholder="이름/나이/직업\n구체적 나쁜 짓 (관객이 '저런 사람 내 주변에도 있어!'라고 할 것)\n숨겨진 비밀 또는 약점",
            height=100, key="villain_input")
        season_question = st.text_input("시즌 질문",
            placeholder="마지막 화까지 답을 안 주는 단 하나의 질문", key="sq_input")

    st.markdown(
        '<div class="callout" style="margin-top:.3rem">'
        '<div class="cl">🎭 감초 캐릭터 힌트 (선택)</div>'
        '<div style="font-size:.75rem;color:var(--dim)">시어머니·시누이·직장동료 등 감초를 미리 알려주면 AI가 더 정교하게 설계합니다.</div>'
        '</div>', unsafe_allow_html=True
    )
    supporting_hint = st.text_area("감초 캐릭터 힌트",
        placeholder="예: 시어머니(분노유발) — 냉정하고 계산적\n예: 직장동료 지수(정보투하) — 밝고 수다스러움\n예: 친구 미래(감정증폭) — 직설적, 주인공 편",
        height=70, label_visibility="collapsed", key="hint_input")

    custom_idea = st.text_area("커스텀 아이디어 (선택)",
        placeholder="공식 변형 또는 특별한 설정", height=50, key="custom_input")

    if st.button("✨ 빈 칸 자동 채우기 — 적어 둔 칸은 그대로 두고 나머지를 AI가 채웁니다",
                 use_container_width=True, key="fill_blank_btn"):
        cur_now = current_concept_fields()
        if not any(cur_now.values()):
            st.error("한 칸이라도 먼저 적어 주세요. 한 문장 전제만 있어도 됩니다.")
        elif all(cur_now[f] for f in cur_now if f != "custom_idea"):
            st.info("빈 칸이 없습니다.")
        else:
            with st.spinner("빈 칸을 채우는 중... (20~40초)"):
                if run_field_fill("", "적어 둔 칸에서 채움", fill_missing=True, overwrite=False):
                    st.rerun()

    if st.button("🧠 컨셉 + 도파민 + 감초 설계 생성", type="primary", use_container_width=True):
        premise_ok = True
        if premise.strip():
            pc = st.session_state.premise_check
            if not pc or pc.get("premise") != premise:
                with st.spinner("전제 점검 중..."):
                    run_premise_check(premise)
            res = (st.session_state.premise_check or {}).get("result") or {}
            premise_ok = bool(res.get("pass")) or skip_premise or not res
        if not premise.strip() and not (protagonist and villain and season_question):
            st.error("한 문장 전제를 입력하세요. 전제가 없으면 주인공 / 악역 / 시즌 질문을 모두 입력해야 합니다.")
        elif paywall_key > total_eps - 3:
            st.error(f"첫 과금 관문(EP {paywall_key})이 총 {total_eps}화에 비해 너무 뒤입니다. EP {total_eps - 3} 이하로 낮추세요.")
        elif not premise_ok:
            show_premise_check()
            st.error("전제에 빠진 것이 있습니다. 전제를 고치거나 '전제 점검에 걸려도 그대로 컨셉 생성'을 체크하세요.")
        else:
            protagonist = protagonist or "전제에서 설계한다."
            villain = villain or "전제에서 설계한다."
            season_question = season_question or "전제에서 뽑는다."
            combined = custom_idea
            if supporting_hint:
                combined += f"\n[감초 힌트]\n{supporting_hint}"
            with st.spinner("컨셉 + 도파민 + 감초 설계 중... (20~40초)"):
                raw = call_claude(
                    P.build_concept_prompt(formula_key, protagonist, villain,
                                           secrets or "자동 생성", season_question,
                                           combined, market, rating,
                                           producer_note=st.session_state.producer_note,
                                           premise=premise, total_eps=total_eps,
                                           **common_opts()),
                    MAX_TOKENS_CONCEPT
                )
                result = safe_json(raw)
                if result:
                    result["total_eps"] = total_eps
                    st.session_state.author_fixed = custom_idea
                    st.session_state.concept = result
                    st.session_state.step = 1
                    st.rerun()
                else:
                    st.error("생성 실패. 다시 시도하세요.")
                    with st.expander("Raw"): st.text(raw[:1000])

    # ── 컨셉 결과 ──────────────────────────────────
    if st.session_state.concept:
        c = st.session_state.concept
        st.markdown("---")
        st.markdown(f'<div class="sec">📋 {c.get("title","")} — 컨셉 완성</div>', unsafe_allow_html=True)

        col_c1, col_c2 = st.columns([2,1])
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
            st.markdown('<div class="sec">🧠 도파민 설계</div>', unsafe_allow_html=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if dd.get("primary_triggers"):
                    tr = "".join([f'<div style="font-size:.85rem;margin:.2rem 0">• {t}</div>' for t in dd["primary_triggers"]])
                    st.markdown(f'<div class="card" style="border-left:4px solid var(--orange)"><div class="cl">🧠 주력 도파민 트리거</div>{tr}</div>', unsafe_allow_html=True)
                if dd.get("addiction_loop"):
                    st.markdown(f'<div class="ri"><div class="rl">🔄 중독 루프</div>{dd["addiction_loop"]}</div>', unsafe_allow_html=True)
            with col_d2:
                if dd.get("seesaw_pattern"):
                    st.markdown(f'<div class="ri"><div class="rl">⚖️ 감정 시소</div>{dd["seesaw_pattern"]}</div>', unsafe_allow_html=True)
                if dd.get("reversal_timing"):
                    st.markdown(f'<div class="ri"><div class="rl">💥 역전 타이밍</div>{dd["reversal_timing"]}</div>', unsafe_allow_html=True)
                if dd.get("reveal_schedule"):
                    st.markdown(f'<div class="ri"><div class="rl">🔓 비밀 드러남</div>{dd["reveal_schedule"]}</div>', unsafe_allow_html=True)

        # 주인공 / 악역
        col_p, col_v = st.columns(2)
        with col_p:
            p = c.get("protagonist",{})
            st.markdown(
                f'<div class="card"><div class="cl">🔥 주인공: {p.get("name","")} ({p.get("age","")})</div>'
                f'<div style="font-size:.8rem;color:var(--r)">시작: {p.get("start_state","")}</div>'
                f'<div style="font-size:.85rem;margin:.3rem 0">{p.get("identity","")}</div>'
                f'<div style="font-size:.8rem;color:var(--navy);font-weight:700">🎭 숨겨진 힘: {p.get("hidden_power","")}</div>'
                f'<div style="font-size:.8rem;color:var(--dim);margin-top:.3rem">{p.get("secret","")}</div>'
                f'<div style="font-size:.8rem;color:var(--g)">아크: {p.get("arc","")}</div>'
                f'</div>', unsafe_allow_html=True
            )
        with col_v:
            v = c.get("villain",{})
            st.markdown(
                f'<div class="card" style="border-left:4px solid var(--r)">'
                f'<div class="cl">🖤 악역: {v.get("name","")} ({v.get("age","")})</div>'
                f'<div style="font-size:.85rem">{v.get("identity","")}</div>'
                f'<div style="font-size:.8rem;color:var(--r);font-weight:700;margin-top:.3rem">구체적 나쁜 짓: {v.get("specific_evil","")}</div>'
                f'<div style="font-size:.8rem;color:var(--dim)">몰락: {v.get("downfall","")}</div>'
                f'</div>', unsafe_allow_html=True
            )

        # 조력자 / 경쟁자
        col_h, col_ri = st.columns(2)
        with col_h:
            h = c.get("helper",{})
            if h.get("name"):
                st.markdown(
                    f'<div class="ri"><div class="rl">💙 조력자: {h.get("name","")}</div>'
                    f'{h.get("role","")}<br>'
                    f'<span style="font-size:.75rem;color:var(--orange)">⚠️ 숨겨진 의도: {h.get("hidden_agenda","")}</span></div>',
                    unsafe_allow_html=True
                )
        with col_ri:
            ri = c.get("rival",{})
            if ri.get("name"):
                st.markdown(
                    f'<div class="ri"><div class="rl">🥊 경쟁자: {ri.get("name","")}</div>'
                    f'일시적 우위: {ri.get("advantage","")}<br>'
                    f'<span style="font-size:.75rem;color:var(--dim)">{ri.get("purpose","")}</span></div>',
                    unsafe_allow_html=True
                )

        # 감초 캐릭터
        sc_list = [s for s in c.get("supporting_cast",[]) if s.get("name") or s.get("relation")]
        if sc_list:
            st.markdown('<div class="sec">🎭 감초 캐릭터 <span class="en">SUPPORTING CAST</span></div>', unsafe_allow_html=True)
            func_c = {"A분노유발":"var(--r)","B정보투하":"#E65100","C감정증폭":"var(--g)"}
            func_l = {"A분노유발":"🔴 분노 유발기","B정보투하":"🟡 정보 투하기","C감정증폭":"🟢 감정 증폭기"}
            sc_cols = st.columns(min(len(sc_list),3))
            for idx,sc in enumerate(sc_list[:3]):
                with sc_cols[idx]:
                    nm = sc.get("name") or sc.get("relation","")
                    fn = sc.get("function","")
                    fc = func_c.get(fn,"var(--dim)")
                    fl = func_l.get(fn,fn)
                    st.markdown(
                        f'<div class="card" style="border-left:3px solid {fc}">'
                        f'<div class="cl">{fl}</div>'
                        f'<div style="font-weight:700;font-size:.9rem">{nm}</div>'
                        f'<div style="font-size:.75rem;color:var(--dim)">{sc.get("relation","")} | {sc.get("appear_ep","")}</div>'
                        f'<div style="font-size:.82rem;margin-top:.4rem;font-style:italic">"{sc.get("dialogue_tone","")}"</div>'
                        f'<div style="font-size:.72rem;color:{fc};margin-top:.2rem">{sc.get("dopamine_role","")}</div>'
                        f'</div>', unsafe_allow_html=True
                    )
            if c.get("character_bible_note"):
                st.markdown(f'<div class="callout"><div class="cl">캐릭터 관계 요약</div>{c["character_bible_note"]}</div>', unsafe_allow_html=True)

        # 과금 설계
        pd = c.get("paywall_design",{})
        market_note = f'<div style="font-size:.75rem;color:#D32F2F;margin-top:.2rem">🌐 {pd.get("ep16_market","")}</div>' if pd.get("ep16_market") else ""
        st.markdown(
            f'<div class="card" style="border-left:4px solid var(--y)">'
            f'<div class="cl">💰 과금 전환점 (EP {paywall_key}~{paywall_key + 4})</div>'
            f'<div style="font-size:.95rem;font-weight:700">{pd.get("ep16_reversal","")}</div>'
            f'<div style="margin-top:.3rem">{d_badge(pd.get("ep16_dopamine",""))}</div>'
            f'{market_note}'
            f'<div style="font-size:.85rem;color:var(--dim);margin-top:.3rem">EP 20: {pd.get("ep20_cliffhanger","")}</div>'
            f'</div>', unsafe_allow_html=True
        )

        # 비밀 스케줄
        secs = [s for s in c.get("secrets",[]) if s.get("secret")]
        if secs:
            s_html = "".join([
                f'<div style="font-size:.85rem;margin:.3rem 0">• EP{s.get("reveal_ep","?")} — {s.get("secret","")} → {s.get("impact","")} {d_badge(s.get("dopamine_type",""))}</div>'
                for s in secs
            ])
            st.markdown(f'<div class="ri"><div class="rl">🔒 비밀 공개 스케줄</div>{s_html}</div>', unsafe_allow_html=True)

        # 장소 설계
        ld = c.get("location_design",{})
        if ld:
            st.markdown('<div class="sec">📍 장소 설계</div>', unsafe_allow_html=True)
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                main_locs = ld.get("main_locations",[])
                if main_locs:
                    lh = "".join([
                        f'<div style="font-size:.85rem;margin:.3rem 0"><b>{l.get("name","")}</b> — {l.get("emotion_role","")}<br>'
                        f'<span style="font-size:.72rem;color:var(--orange)">도파민: {l.get("dopamine_scene","")}</span></div>'
                        for l in main_locs if l.get("name")
                    ])
                    st.markdown(f'<div class="ri"><div class="rl">🏠 주 장소</div>{lh}</div>', unsafe_allow_html=True)
                if ld.get("sub_locations"):
                    st.markdown(f'<div class="ri"><div class="rl">📌 보조 장소</div>{" · ".join(ld["sub_locations"])}</div>', unsafe_allow_html=True)
            with col_l2:
                if ld.get("reversal_location"):
                    st.markdown(f'<div class="ri" style="border-left:3px solid var(--g)"><div class="rl" style="color:var(--g)">💥 역전 장소</div>{ld["reversal_location"]}</div>', unsafe_allow_html=True)
                if ld.get("cliffhanger_location"):
                    st.markdown(f'<div class="ri" style="border-left:3px solid var(--r)"><div class="rl" style="color:var(--r)">⚡ 클리프행어 장소</div>{ld["cliffhanger_location"]}</div>', unsafe_allow_html=True)
                if ld.get("romance_peak"):
                    st.markdown(f'<div class="ri" style="border-left:3px solid var(--pink)"><div class="rl" style="color:var(--pink)">💕 로맨스 피크</div>{ld["romance_peak"]}</div>', unsafe_allow_html=True)

    # ── STEP 2: 아크 ────────────────────────────────
    if st.session_state.step >= 1 and st.session_state.concept:
        st.markdown("---")
        st.markdown('<div class="section-header">📊 시즌 아크 설계 <span class="en">STEP 2 · SEASON ARC</span></div>', unsafe_allow_html=True)

        _n_eps = int(st.session_state.concept.get("total_eps", 100))
        if st.button(f"📊 {_n_eps}화 아크 + 도파민 마일스톤 생성 ({math.ceil(_n_eps / 25)}회 분할)", type="primary", use_container_width=True):
            total = st.session_state.concept.get("total_eps",100)
            arc_progress = st.empty()
            result = generate_arc_chunks(
                st.session_state.concept, total,
                note_with_fixed(), arc_progress)
            if result:
                st.session_state.arc = result
                st.session_state.step = 2
                st.rerun()

        if st.session_state.arc:
            arc = st.session_state.arc
            st.markdown(f'<div class="callout"><div class="cl">아크 요약</div>{arc.get("arc_summary","")}</div>', unsafe_allow_html=True)

            # 도파민 마일스톤
            ms = arc.get("dopamine_milestones",[])
            if ms:
                with st.expander(f"🧠 도파민 마일스톤 {len(ms)}개"):
                    for m in ms:
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--border)">'
                            f'<div style="min-width:50px;font-weight:700;font-size:.85rem">EP {m.get("ep","")}</div>'
                            f'{d_badge(m.get("type",""))}'
                            f'<div style="font-size:.85rem">{m.get("event","")}</div>'
                            f'</div>', unsafe_allow_html=True
                        )

            # 100화 테이블
            blocks = arc.get("blocks",[])
            if blocks:
                rows = ""
                for blk in blocks:
                    for ep in blk.get("episodes",[]):
                        ep_no = ep.get("ep",0)
                        paywall = ep_no in arc.get("paywall_eps", list(range(paywall_key, paywall_key + 5)))
                        badge = '<span style="background:var(--y);color:var(--navy);padding:1px 5px;border-radius:8px;font-size:.62rem;font-weight:800">💰</span>' if paywall else (
                            '<span style="background:var(--g);color:white;padding:1px 5px;border-radius:8px;font-size:.62rem;font-weight:800">FREE</span>' if ep_no<=15 else "")
                        em = ep.get("emotion_mode","")
                        mode = P.EMOTIONAL_MODES.get(em,{})
                        mc = CAT_COLOR.get(P.EMOTION_CATEGORIES.get(mode.get("category","怒 분노계"),{}).get("name","")+"계","#888") if mode else "#888"
                        # category lookup
                        cat = mode.get("category","")
                        mc = "#D32F2F" if cat=="怒" else "#7B68EE" if cat=="哀" else "#FF69B4" if cat=="喜" else "#2EC484" if cat=="樂" else "#FF8C00" if cat=="張" else "#888"
                        cc = {"Slap":"#D32F2F","Reveal":"#7B68EE","Reversal":"#FF8C00",
                              "Arrival":"#2EC484","Choice":"#191970","Threat":"#D32F2F","Tears":"#FF69B4"}.get(ep.get("cliffhanger_type",""),"#888")
                        rows += (
                            f'<tr style="border-bottom:1px solid #E6E9EF">'
                            f'<td style="padding:5px 8px;font-weight:700;white-space:nowrap">EP{ep_no} {badge}</td>'
                            f'<td style="padding:5px 8px;font-size:.8rem">{ep.get("summary","")}</td>'
                            f'<td style="padding:5px 8px;font-size:.75rem;color:{mc}">{mode.get("emoji","")} {em}</td>'
                            f'<td style="padding:5px 8px;font-size:.75rem;font-weight:700;color:{cc}">{ep.get("cliffhanger_type","")}</td>'
                            f'<td style="padding:5px 8px;font-size:.72rem;color:var(--orange)">{ep.get("dopamine_moment","")[:25]}</td>'
                            f'</tr>'
                        )

                st.markdown(
                    f'<div style="overflow-x:auto;max-height:480px;overflow-y:auto">'
                    f'<table style="width:100%;border-collapse:collapse;font-family:var(--body)">'
                    f'<thead style="position:sticky;top:0;background:#191970">'
                    f'<tr><th style="padding:7px 8px;color:#FFCB05;font-size:.72rem;text-align:left">EP</th>'
                    f'<th style="padding:7px 8px;color:#FFCB05;font-size:.72rem;text-align:left">핵심 사건</th>'
                    f'<th style="padding:7px 8px;color:#FFCB05;font-size:.72rem;text-align:left">감정 모드</th>'
                    f'<th style="padding:7px 8px;color:#FFCB05;font-size:.72rem;text-align:left">클리프행어</th>'
                    f'<th style="padding:7px 8px;color:#FFCB05;font-size:.72rem;text-align:left">🧠 도파민</th>'
                    f'</tr></thead>'
                    f'<tbody style="background:var(--card)">{rows}</tbody>'
                    f'</table></div>', unsafe_allow_html=True
                )

                # 아크 다운로드
                arc_txt = f"BLUE JEANS SHORTFORM ENGINE v2.8 — {st.session_state.concept.get('title','')}\n"
                arc_txt += f"아크: {arc.get('arc_summary','')}\n\n"
                for blk in blocks:
                    arc_txt += f"[{blk.get('ep_range','')} — {blk.get('phase','')} / {blk.get('sweet_bitter','')} / {blk.get('dopamine_target','')}]\n"
                    for ep in blk.get("episodes",[]):
                        arc_txt += f"  EP{ep.get('ep','')}: {ep.get('summary','')} | {ep.get('emotion_mode','')} | {ep.get('cliffhanger_type','')}: {ep.get('cliffhanger','')}\n"
                    arc_txt += "\n"
                st.download_button("⬇️ 아크 TXT", arc_txt.encode("utf-8"),
                    file_name=f"arc_{st.session_state.concept.get('title','')}.txt", mime="text/plain")

    # ── STEP 3: 집필 ────────────────────────────────
    if st.session_state.step >= 2 and st.session_state.arc:
        st.markdown("---")
        st.markdown('<div class="section-header">✍️ 블록 집필 <span class="en">STEP 3 · BLOCK WRITING</span></div>', unsafe_allow_html=True)

        blocks = st.session_state.arc.get("blocks",[])

        # 25가지 감정 모드 레퍼런스
        with st.expander("🎭 25가지 감정 모드 레퍼런스", expanded=False):
            for cat_name, mode_keys in P.EMOTION_BY_CATEGORY.items():
                cc = CAT_COLOR.get(cat_name, "#888")
                st.markdown(f'<div style="font-size:.8rem;font-weight:800;color:{cc};margin:.8rem 0 .3rem;border-bottom:1px solid {cc};padding-bottom:3px">{cat_name}</div>', unsafe_allow_html=True)
                mc = st.columns(len(mode_keys))
                for ci, mk in enumerate(mode_keys):
                    m = P.EMOTIONAL_MODES.get(mk,{})
                    with mc[ci]:
                        st.markdown(
                            f'<div style="background:var(--card);border:1px solid var(--border);'
                            f'border-top:3px solid {cc};border-radius:0 0 8px 8px;padding:.5rem .6rem">'
                            f'<div style="font-weight:800;font-size:.82rem">{m.get("emoji","")} {mk}</div>'
                            f'<div style="font-size:.68rem;color:var(--dim);margin:.15rem 0">{m.get("desc","")[:35]}</div>'
                            f'<div style="font-size:.65rem;color:{cc}">{m.get("dopamine","")[:28]}</div>'
                            f'<div style="font-size:.62rem;color:var(--dim);margin-top:.2rem;font-style:italic">📍 {m.get("arc_position","")}</div>'
                            f'</div>', unsafe_allow_html=True
                        )

        # 콤보 추천 + 커스텀 설정
        combo_options = {
            "직접 설정": None,
            "💢 분노 축적 (EP 1~15)":    P.EMOTIONAL_MODE_COMBOS["분노_축적"],
            "⚖️ 감정 시소 (EP 15~40)":   P.EMOTIONAL_MODE_COMBOS["감정_시소"],
            "💰 과금 전환 (과금 관문 구간)":   P.EMOTIONAL_MODE_COMBOS["과금_전환"],
            "🔥 로맨스 피크 (EP 30~50)":  P.EMOTIONAL_MODE_COMBOS["로맨스_피크"],
            "💚 삼각관계 (EP 20~50)":    P.EMOTIONAL_MODE_COMBOS["삼각관계"],
            "⚔️ 복수 시작 (EP 40~70)":   P.EMOTIONAL_MODE_COMBOS["복수_시작"],
            "🌊 클라이맥스 (EP 80~100)":  P.EMOTIONAL_MODE_COMBOS["클라이맥스"],
        }

        with st.expander("🎛️ 블록별 감정 모드 설정", expanded=False):
            st.caption("대분류 → 세부 감정 2단계 선택. 화별로 최대 도파민 감정을 지정하세요.")

            col_tb, col_cb = st.columns([1,2])
            with col_tb:
                target_bn = st.selectbox("수정할 블록",
                    [b.get("block_no",i+1) for i,b in enumerate(blocks)],
                    format_func=lambda x:f"블록{x} — {blocks[x-1].get('ep_range','') if x<=len(blocks) else ''}")
            with col_cb:
                combo_key = st.selectbox("추천 콤보 적용", list(combo_options.keys()), key="ck")

            if target_bn:
                if combo_options.get(combo_key):
                    current = combo_options[combo_key]
                else:
                    current = st.session_state.block_modes.get(target_bn, P.EMOTIONAL_MODE_COMBOS["분노_축적"])

                ep_base = (target_bn-1)*5+1
                new_modes = []
                mc = st.columns(5)

                for ci, col in enumerate(mc):
                    with col:
                        st.markdown(f'<div style="font-size:.75rem;font-weight:700;text-align:center">EP{ep_base+ci}</div>', unsafe_allow_html=True)
                        cur_m = current[ci] if ci < len(current) else "굴욕"
                        cat_names = list(P.EMOTION_BY_CATEGORY.keys())
                        cur_cat = next((cat for cat,keys in P.EMOTION_BY_CATEGORY.items() if cur_m in keys), cat_names[0])
                        cat_idx = cat_names.index(cur_cat) if cur_cat in cat_names else 0

                        sel_cat = st.selectbox("분류", cat_names, index=cat_idx,
                            key=f"cat_{target_bn}_{ci}", label_visibility="collapsed")
                        detail = P.EMOTION_BY_CATEGORY.get(sel_cat,[])
                        det_idx = detail.index(cur_m) if cur_m in detail else 0
                        sel_m = st.selectbox("감정", detail,
                            format_func=lambda x:f"{P.EMOTIONAL_MODES[x]['emoji']} {x}",
                            index=det_idx, key=f"em_{target_bn}_{ci}", label_visibility="collapsed")
                        new_modes.append(sel_m)

                        m_info = P.EMOTIONAL_MODES.get(sel_m,{})
                        cat_c = CAT_COLOR.get(sel_cat,"#888")
                        st.markdown(
                            f'<div style="font-size:.65rem;color:{cat_c};margin-top:.2rem">{m_info.get("dopamine","")[:32]}</div>'
                            f'<div style="font-size:.62rem;color:var(--dim);font-style:italic">"{m_info.get("good_scene","")[:38]}..."</div>',
                            unsafe_allow_html=True
                        )

                if st.button("✅ 저장", key="save_m", type="primary"):
                    st.session_state.block_modes[target_bn] = new_modes
                    emojis = " ".join([P.EMOTIONAL_MODES[m]["emoji"] for m in new_modes])
                    st.success(f"블록 {target_bn} 저장: {emojis}")
                    st.rerun()

        st.caption("블록 1개 = 5화. 아래에서 블록을 선택하면 상세 정보와 각본 쓰기 버튼이 나타납니다.")

        # 진행률
        done_count = len(st.session_state.blocks)
        total_blocks = len(blocks)
        if total_blocks > 0:
            pct = int(done_count / total_blocks * 100)
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem">'
                f'<div style="font-size:.82rem;color:var(--dim)">{done_count}/{total_blocks} 블록 완료</div>'
                f'<div style="font-size:.82rem;color:var(--dim)">{pct}%</div></div>'
                f'<div style="background:#E6E9EF;height:6px;border-radius:3px;margin-bottom:1rem">'
                f'<div style="background:var(--g);height:6px;border-radius:3px;width:{pct}%"></div></div>',
                unsafe_allow_html=True
            )

        # 블록 그리드 (선택용)
        for row_start in range(0, len(blocks), 5):
            cols = st.columns(5)
            for ci, col in enumerate(cols):
                bi = row_start + ci
                if bi >= len(blocks): break
                blk = blocks[bi]
                bn = blk.get("block_no", bi+1)
                ep_r = blk.get("ep_range","")
                phase = blk.get("phase","")
                is_done = bn in st.session_state.blocks
                is_selected = st.session_state.selected_block == bn
                is_paywall = block_has_paywall(bn)
                default_modes = default_block_modes(bn, blk)

                mode_disp = " ".join([P.EMOTIONAL_MODES.get(m,{}).get("emoji","") for m in default_modes[:5]])

                with col:
                    st.markdown(
                        f'<div style="font-size:.62rem;color:var(--dim);text-align:center;margin-bottom:2px">'
                        f'{ep_r}<br>{mode_disp}</div>',
                        unsafe_allow_html=True
                    )
                    if is_done:
                        label = f"✅ 블록{bn}"
                    elif is_selected:
                        label = f"▶ 블록{bn}"
                    else:
                        label = f"블록{bn}"
                    pay = " 💰" if is_paywall else ""
                    if st.button(f"{label}{pay}\n{phase}", key=f"b_{bn}", use_container_width=True):
                        st.session_state.selected_block = bn
                        st.rerun()

        # 선택된 블록 상세 패널
        sel = st.session_state.selected_block
        if sel and sel <= len(blocks):
            blk = blocks[sel-1]
            bn = sel
            ep_r = blk.get("ep_range","")
            phase = blk.get("phase","")
            theme = blk.get("theme","")
            sweet_bitter = blk.get("sweet_bitter","")
            dopamine_target = blk.get("dopamine_target","")
            is_done = bn in st.session_state.blocks

            default_modes = default_block_modes(bn, blk)
            mode_disp = " ".join([P.EMOTIONAL_MODES.get(m,{}).get("emoji","") for m in default_modes[:5]])

            st.markdown("---")
            st.markdown(
                f'<div style="background:var(--lb);border-left:4px solid var(--navy);'
                f'border-radius:0 8px 8px 0;padding:1rem 1.2rem;margin-bottom:1rem">'
                f'<div style="font-weight:800;font-size:1rem;color:var(--navy);margin-bottom:.5rem">'
                f'블록{bn} — {ep_r}</div>'
                f'<div style="font-size:.85rem;margin:.2rem 0">국면: {phase} / {theme}</div>'
                f'<div style="font-size:.85rem;margin:.2rem 0">감정 리듬: {sweet_bitter} / 도파민: {dopamine_target}</div>'
                f'<div style="font-size:.85rem;margin:.2rem 0">감정 모드: {mode_disp}</div>'
                f'</div>', unsafe_allow_html=True
            )

            # 에피소드 목록
            episodes = blk.get("episodes", [])
            if episodes:
                ep_html = ""
                for ep in episodes:
                    em = ep.get("emotion_mode","")
                    mode = P.EMOTIONAL_MODES.get(em,{})
                    ep_html += (
                        f'<div style="display:flex;gap:8px;padding:4px 0;border-bottom:1px solid #E6E9EF;font-size:.82rem">'
                        f'<div style="min-width:45px;font-weight:700;color:var(--navy)">EP{ep.get("ep","")}</div>'
                        f'<div style="flex:1">{ep.get("summary","")}</div>'
                        f'<div style="min-width:30px">{mode.get("emoji","")}</div>'
                        f'<div style="min-width:60px;color:var(--orange);font-size:.75rem">{ep.get("cliffhanger_type","")}</div>'
                        f'</div>'
                    )
                st.markdown(f'<div style="margin-bottom:1rem">{ep_html}</div>', unsafe_allow_html=True)

            if is_done:
                st.success(f"블록{bn} 집필 완료")
                show_block_check(bn)
                with st.expander(f"📖 블록{bn} 대본 보기", expanded=False):
                    st.markdown(highlight_script(st.session_state.blocks[bn]), unsafe_allow_html=True)
                col_dl, col_re, col_del = st.columns(3)
                with col_dl:
                    block_docx = build_docx(st.session_state.blocks[bn],
                        title=f"블록{bn} — {ep_r}", subtitle=phase)
                    st.download_button(f"⬇️ 블록{bn} DOCX", block_docx,
                        file_name=f"block{bn:02d}_{ep_r.replace(' ','')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_{bn}", use_container_width=True)
                with col_re:
                    if st.button(f"🔄 블록{bn} 다시 쓰기", key=f"re_{bn}", use_container_width=True):
                        del st.session_state.blocks[bn]
                        st.session_state.block_checks.pop(bn, None)
                        st.rerun()
                with col_del:
                    if st.button(f"🗑️ 삭제", key=f"del_{bn}", use_container_width=True):
                        del st.session_state.blocks[bn]
                        st.session_state.block_checks.pop(bn, None)
                        st.session_state.selected_block = None
                        st.rerun()
            else:
                if st.button(
                    f"✍️ 블록{bn} 각본 쓰기 — {ep_r} ({phase})",
                    type="primary", use_container_width=True, key=f"write_{bn}"
                ):
                    prev_s = ""
                    if bn > 1 and (bn-1) in st.session_state.blocks:
                        t = st.session_state.blocks[bn-1]
                        prev_s = t[-300:] if len(t)>300 else t
                    _ledger = arc_ledger(st.session_state.arc.get("blocks", []), before_ep=(bn - 1) * 5 + 1)
                    if _ledger:
                        prev_s = "[앞에서 일어난 일 — 화별]\n" + _ledger + ("\n\n[직전 원고의 끝]\n" + prev_s if prev_s else "")
                    with st.spinner(f"블록{bn} {mode_disp} 각본 집필 중... (Opus)"):
                        def make_prompt(rewrite_note="", _blk=blk, _bn=bn, _prev=prev_s, _modes=default_modes):
                            return P.build_block_prompt(
                                st.session_state.concept, _blk, _bn, _prev,
                                emotional_modes=_modes,
                                producer_note=note_with_fixed(),
                                premise=st.session_state.premise,
                                rewrite_note=rewrite_note, **common_opts())
                        rt, check = write_block_checked(make_prompt, st.session_state.concept, bn)
                        st.session_state.blocks[bn] = rt
                        st.session_state.block_checks[bn] = check
                        st.rerun()

        # 집필된 블록 요약 (상세는 블록 선택 패널에서)
        if st.session_state.blocks:
            st.markdown("---")
            done_list = sorted(st.session_state.blocks.keys())
            st.markdown(
                f'<div style="font-size:.82rem;color:var(--dim)">'
                f'📝 집필 완료: {", ".join([f"블록{b}" for b in done_list])} '
                f'— 위 그리드에서 블록을 클릭하면 대본을 확인할 수 있습니다.</div>',
                unsafe_allow_html=True
            )

    # ── STEP 4: 다운로드 ────────────────────────────
    if st.session_state.blocks:
        st.markdown("---")
        st.markdown('<div class="section-header">⬇️ 다운로드 <span class="en">STEP 4 · DOWNLOAD</span></div>', unsafe_allow_html=True)

        total_b = len(st.session_state.blocks)
        st.success(f"✅ {total_b}개 블록 완성 — 약 {total_b*5}화 대본")

        title = st.session_state.concept.get("title","shortform") if st.session_state.concept else "shortform"
        full = f"👖 BLUE JEANS SHORTFORM ENGINE v2.8\n제목: {title}\n"
        if st.session_state.concept:
            full += f"로그라인: {st.session_state.concept.get('logline','')}\n"
            dd = st.session_state.concept.get("dopamine_design",{})
            full += f"중독 루프: {dd.get('addiction_loop','')}\n"
        full += f"생성일: {datetime.now().strftime('%Y-%m-%d')}\n{'='*60}\n\n"

        blocks_ref = st.session_state.arc.get("blocks",[]) if st.session_state.arc else []
        for bn in sorted(st.session_state.blocks.keys()):
            bi_info = blocks_ref[bn-1] if bn<=len(blocks_ref) else {}
            ep_r = bi_info.get("ep_range",f"블록{bn}")
            full += f"\n{'='*60}\n[블록{bn} — {ep_r}]\n{'='*60}\n\n"
            full += st.session_state.blocks[bn] + "\n\n"

        col_dl1, col_dl2, col_dl3, col_dl4 = st.columns(4)
        with col_dl1:
            docx_bytes = build_docx(full, title=title,
                subtitle=st.session_state.concept.get('logline','') if st.session_state.concept else '')
            st.download_button("📄 전체 대본 DOCX", docx_bytes,
                file_name=f"{safe_name(title)}_전체대본.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True)
        with col_dl2:
            st.download_button("📄 전체 대본 TXT", full.encode("utf-8"),
                file_name=f"{safe_name(title)}_전체대본.txt", mime="text/plain", use_container_width=True)
        with col_dl3:
            if st.session_state.arc:
                csv_lines = ["EP,핵심사건,감정모드,클리프행어유형,클리프행어,도파민,과금"]
                for blk in st.session_state.arc.get("blocks",[]):
                    for ep in blk.get("episodes",[]):
                        pay = "Y" if ep.get("ep",0) in st.session_state.arc.get("paywall_eps",[]) else "N"
                        csv_lines.append(
                            f"EP{ep.get('ep','')},{ep.get('summary','').replace(',','；')},"
                            f"{ep.get('emotion_mode','')},{ep.get('cliffhanger_type','')},"
                            f"{ep.get('cliffhanger','').replace(',','；')},"
                            f"{ep.get('dopamine_moment','').replace(',','；')},{pay}"
                        )
                st.download_button("📊 아크 CSV", "\n".join(csv_lines).encode("utf-8-sig"),
                    file_name=f"{safe_name(title)}_아크.csv", mime="text/csv", use_container_width=True)
        with col_dl3:
            if st.button("🔄 전체 초기화", use_container_width=True):
                for k in ["step","concept","arc","blocks","convert_result","block_modes","pilot_text"]:
                    st.session_state[k] = 0 if k=="step" else {} if k in ["blocks","block_modes"] else None
                st.rerun()


# ═══════════════════════════════════════════════════
#  TAB 2: 기존 글 → 숏폼 변환
# ═══════════════════════════════════════════════════
with tab_convert:
    st.markdown("---")
    st.markdown('<div class="section-header">🔄 기존 글 → 숏폼 변환 <span class="en">CONVERT TO SHORTFORM</span></div>', unsafe_allow_html=True)
    st.caption("소설·시나리오·웹툰·실화 등 어떤 텍스트든 도파민 탑재 숏폼으로 변환합니다.")

    col_cv1, col_cv2 = st.columns([2,1])
    with col_cv1:
        source_text = st.text_area("원본 텍스트 붙여넣기",
            placeholder="소설 일부, 시나리오, 기사, 줄거리 등 최대 3,000자.", height=160)
        preserve_elements = st.text_area("보존할 원작 요소 (선택)",
            placeholder="원작에서 반드시 살릴 감성·설정·캐릭터\n예: 단짠단짠 감성, 취준생 현실감, 캠퍼스+오피스 교차",
            height=60)
    with col_cv2:
        cv_formula = st.selectbox("막장 공식",
            list(P.MAKJANG_FORMULAS.keys()),
            format_func=lambda x:P.MAKJANG_FORMULAS[x]["name"], key="cvf")
        cv_intensity = st.selectbox("변환 강도",
            list(P.CONVERT_INTENSITY.keys()),
            format_func=lambda x:P.CONVERT_INTENSITY[x]["name"],
            index=2, key="cvi")
        col_m2, col_r2 = st.columns(2)
        with col_m2:
            cv_market = st.selectbox("시장",["한국","글로벌","중국"], key="cvm")
        china_tone_notice(cv_market)
        with col_r2:
            cv_rating = st.selectbox("수위",["family","teen","adult"],
                format_func=lambda x:{"family":"전체가","teen":"15세+","adult":"19+"}[x],
                index=1, key="cvr")
        cv_eps = st.selectbox("목표 화수",[20,30,50,100],index=1, key="cve")

        ii = P.CONVERT_INTENSITY[cv_intensity]
        st.markdown(f'<div class="ri" style="border-left:3px solid var(--orange)"><div class="rl" style="color:var(--orange)">변환 강도</div><div style="font-size:.75rem">{ii["desc"]}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ri" style="border-left:3px solid var(--orange)"><div class="rl" style="color:var(--orange)">🧠 도파민</div><div style="font-size:.75rem">{P.MAKJANG_FORMULAS[cv_formula]["dopamine_key"][:60]}...</div></div>', unsafe_allow_html=True)

    if st.button("🔄 도파민 탑재 숏폼으로 변환", type="primary", use_container_width=True, key="btn_cv"):
        if not source_text.strip():
            st.error("원본 텍스트를 입력하세요.")
        else:
            with st.spinner("원본 분석 + 도파민 설계 + 숏폼 변환 중... (40~60초)"):
                raw = call_claude(
                    P.build_convert_prompt(source_text, cv_formula, cv_eps,
                                           cv_intensity, preserve_elements, cv_market, cv_rating,
                                           producer_note=st.session_state.producer_note,
                                           **common_opts()),
                    MAX_TOKENS_CONVERT
                )
                result = safe_json(raw)
                if result:
                    st.session_state.convert_result = result
                    st.session_state.pilot_text = None
                    st.rerun()
                else:
                    st.error("변환 실패.")
                    with st.expander("Raw"): st.text(raw[:2000])

    if st.session_state.convert_result:
        cr = st.session_state.convert_result
        st.markdown("---")

        # 원본 분석
        oa = cr.get("original_analysis",{})
        st.markdown("#### 📖 원본 분석")
        col_oa1, col_oa2 = st.columns(2)
        with col_oa1:
            st.markdown(f'<div class="ri"><div class="rl">핵심 갈등</div>{oa.get("core_conflict","")}</div>', unsafe_allow_html=True)
            if oa.get("dopamine_potential"):
                st.markdown(f'<div class="ri" style="border-left:3px solid var(--orange)"><div class="rl" style="color:var(--orange)">🧠 도파민 잠재력</div>{oa["dopamine_potential"]}</div>', unsafe_allow_html=True)
            if oa.get("usable_elements"):
                eh = "".join([f'<div style="font-size:.85rem;margin:.2rem 0">✓ {e}</div>' for e in oa["usable_elements"]])
                st.markdown(f'<div class="ri"><div class="rl">활용 가능 요소</div>{eh}</div>', unsafe_allow_html=True)
        with col_oa2:
            if oa.get("preserved_elements"):
                ph = "".join([f'<div style="font-size:.85rem;margin:.2rem 0">♻ {e}</div>' for e in oa["preserved_elements"]])
                st.markdown(f'<div class="ri" style="border-left:3px solid var(--g)"><div class="rl" style="color:var(--g)">보존 요소</div>{ph}</div>', unsafe_allow_html=True)
            if oa.get("problems"):
                prh = "".join([f'<div style="font-size:.85rem;margin:.2rem 0;color:var(--r)">✗ {p}</div>' for p in oa["problems"]])
                st.markdown(f'<div class="ri"><div class="rl">부적합 이유</div>{prh}</div>', unsafe_allow_html=True)

        # 변환 전략
        cs = cr.get("conversion_strategy",{})
        st.markdown("#### ⚡ 변환 전략 + 도파민 설계")
        col_cs1, col_cs2 = st.columns(2)
        with col_cs1:
            st.markdown(f'<div class="card" style="border-left:4px solid var(--y)"><div class="cl">주인공 재설계</div>{cs.get("protagonist_rewrite","")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card" style="border-left:4px solid var(--r)"><div class="cl">악역 설계</div>{cs.get("villain_injection","")}</div>', unsafe_allow_html=True)
            if cs.get("supporting_cast_design"):
                st.markdown(f'<div class="ri"><div class="rl">🎭 감초 설계</div>{cs["supporting_cast_design"]}</div>', unsafe_allow_html=True)
        with col_cs2:
            dd_cv = cs.get("dopamine_design",{})
            if dd_cv:
                st.markdown(
                    f'<div class="card" style="border-left:4px solid var(--orange)">'
                    f'<div class="cl">🧠 도파민 설계</div>'
                    f'<div style="font-size:.85rem;margin:.2rem 0">주력: {dd_cv.get("primary_trigger","")}</div>'
                    f'<div style="font-size:.85rem;margin:.2rem 0">루프: {dd_cv.get("addiction_loop","")}</div>'
                    f'<div style="font-size:.85rem;margin:.2rem 0">역전: {dd_cv.get("reversal_timing","")}</div>'
                    f'<div style="font-size:.85rem;margin:.2rem 0">시소: {dd_cv.get("seesaw","")}</div>'
                    f'</div>', unsafe_allow_html=True
                )
            if cs.get("paywall_moment"):
                st.markdown(f'<div class="card" style="border-left:4px solid var(--y);background:#FFFEF0"><div class="cl">💰 과금 전환점</div>{cs["paywall_moment"]}</div>', unsafe_allow_html=True)

        # 숏폼 컨셉
        sc = cr.get("shortform_concept",{})
        if sc:
            st.markdown("#### 🎬 숏폼 컨셉")
            st.markdown(f'<div class="callout"><div class="cl">{sc.get("title","")} — 로그라인</div>{sc.get("logline","")}</div>', unsafe_allow_html=True)
            col_sc1, col_sc2 = st.columns(2)
            with col_sc1:
                st.markdown(f'<div class="ri"><div class="rl">EP1 첫 프레임</div>{sc.get("hook_ep1","")}</div>', unsafe_allow_html=True)
                if sc.get("first_subtitle"):
                    st.markdown(f'<div class="ri" style="border-left:3px solid var(--orange)"><div class="rl" style="color:var(--orange)">📱 첫 자막</div>{sc["first_subtitle"]}</div>', unsafe_allow_html=True)
            with col_sc2:
                st.markdown(f'<div class="ri"><div class="rl">Bittersweet 감정 곡선</div>{sc.get("emotional_arc","")}</div>', unsafe_allow_html=True)
                if sc.get("market_hook"):
                    st.markdown(f'<div class="ri" style="border-left:3px solid #D32F2F"><div class="rl" style="color:#D32F2F">🌐 Market Hook</div>{sc["market_hook"]}</div>', unsafe_allow_html=True)

        # EP 맵
        ep_map = cr.get("episode_map",[])
        if ep_map:
            st.markdown("#### 📊 에피소드 맵")
            ep_html = ""
            for ep in ep_map:
                cc = {"Slap":"#D32F2F","Reveal":"#7B68EE","Reversal":"#FF8C00",
                      "Arrival":"#2EC484","Choice":"#191970","Threat":"#D32F2F","Tears":"#FF69B4"}.get(ep.get("cliff_type",""),"#888")
                ems = ep.get("emotion_modes",[])
                em_disp = " ".join([P.EMOTIONAL_MODES.get(m,{}).get("emoji","") for m in ems[:5]]) if ems else ep.get("sweet_bitter","")
                ep_html += (
                    f'<div style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #E6E9EF">'
                    f'<div style="min-width:90px;font-weight:700;font-size:.82rem;color:var(--navy)">{ep.get("ep_range","")}</div>'
                    f'<div style="flex:1;font-size:.82rem">{ep.get("summary","")}</div>'
                    f'<div style="min-width:60px;text-align:center;font-size:.8rem">{em_disp}</div>'
                    f'<div style="min-width:60px;text-align:right;font-size:.75rem;font-weight:700;color:{cc}">{ep.get("cliff_type","")}</div>'
                    f'</div>'
                )
            st.markdown(f'<div class="card">{ep_html}</div>', unsafe_allow_html=True)

        # 파일럿 EP1 + EP2 (2단계: Opus 집필)
        st.markdown("#### 🎬 파일럿 대본")
        if not st.session_state.pilot_text:
            st.caption("분석 완료. 파일럿 대본을 Opus로 집필합니다.")
            if st.button("✍️ 파일럿 EP1+EP2 집필 (Opus)", type="primary", use_container_width=True, key="btn_pilot"):
                with st.spinner("Opus가 파일럿 EP1+EP2 집필 중... (30~50초)"):
                    pilot_prompt = P.build_pilot_prompt(
                        cr, source_text or "", cv_market, cv_rating,
                        producer_note=st.session_state.producer_note,
                        formula_key=cv_formula, **common_opts())
                    pilot_result = ""
                    pilot_ph = st.empty()
                    for chunk in call_stream(pilot_prompt, MAX_TOKENS_PILOT, model=MODEL_WRITE):
                        pilot_result += chunk
                        if len(pilot_result) % 200 < 10:
                            pilot_ph.text_area("파일럿 집필 중...", pilot_result, height=300,
                                                key=f"pilot_s_{len(pilot_result)}")
                    st.session_state.pilot_text = pilot_result
                    st.rerun()
        else:
            pilot_full = st.session_state.pilot_text
            # EP1 / EP2 분리 시도
            ep2_markers = ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nEP 2",
                           "EP 2 |", "━━━━━━━━━━━\nEP 2"]
            p1, p2 = pilot_full, ""
            for marker in ep2_markers:
                if marker in pilot_full:
                    idx = pilot_full.index(marker)
                    p1 = pilot_full[:idx].strip()
                    p2 = pilot_full[idx:].strip()
                    break

            t1, t2 = st.tabs(["EP 1", "EP 2"])
            with t1:
                st.markdown(
                    f'<div class="ep-block"><div class="ep-hd">EP 1 — 파일럿 (Opus · 도파민 최대치)</div>'
                    f'{highlight_script(p1)}</div>', unsafe_allow_html=True
                )
            with t2:
                if p2:
                    st.markdown(
                        f'<div class="ep-block"><div class="ep-hd">EP 2 — (Opus)</div>'
                        f'{highlight_script(p2)}</div>', unsafe_allow_html=True
                    )
                else:
                    st.caption("EP 2가 분리되지 않았습니다. 전체 대본에서 확인하세요.")

            col_dl1, col_dl2, col_dl3 = st.columns(3)
            with col_dl1:
                out = f"BLUE JEANS SHORTFORM ENGINE v2.8 — 파일럿 (Opus)\n제목: {sc.get('title','')}\n로그라인: {sc.get('logline','')}\n\n{pilot_full}"
                pilot_docx = build_docx(pilot_full,
                    title=f"파일럿 — {sc.get('title','')}",
                    subtitle=sc.get('logline',''))
                st.download_button("⬇️ 파일럿 DOCX", pilot_docx,
                    file_name=f"pilot_{sc.get('title','convert')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True)
            with col_dl2:
                if st.button("🔄 파일럿 다시 쓰기", use_container_width=True, key="re_pilot"):
                    st.session_state.pilot_text = None
                    st.rerun()
            with col_dl3:
                if st.button("이 컨셉으로 100화 만들기 →", use_container_width=True, key="cv2full"):
                    st.session_state.concept = {
                        "title": sc.get("title",""),
                        "logline": sc.get("logline",""),
                        "formula": cv_formula, "market": cv_market, "rating": cv_rating,
                        "season_question": sc.get("logline",""),
                        "protagonist": {"name":"주인공","age":"","arc":sc.get("emotional_arc",""),
                                        "identity":"","hidden_power":cs.get("hidden_identity",""),
                                        "secret":"","dialogue_tone":"","start_state":"","scroll_stop":""},
                        "villain": {"name":"악역","age":"","identity":"",
                                    "specific_evil":cs.get("villain_injection",""),
                                    "why_hateful":"","secret":"","dialogue_tone":"","downfall":""},
                        "helper": {"name":"","role":"","hidden_agenda":"","twist_ep":""},
                        "rival": {"name":"","role":"","advantage":"","purpose":""},
                        "supporting_cast": [],
                        "character_bible_note": "",
                        "dopamine_design": dd_cv if dd_cv else {},
                        "secrets": [],
                        "paywall_design": {"ep16_reversal":cs.get("paywall_moment",""),
                                           "ep16_dopamine":"","ep16_market":"","ep20_cliffhanger":""},
                        "location_design": {"main_locations":[],"sub_locations":[],
                                            "reversal_location":"","cliffhanger_location":"","romance_peak":""},
                        "hook_sentence": sc.get("hook_ep1",""),
                        "first_subtitle": sc.get("first_subtitle",""),
                        "total_eps": 100
                    }
                    st.session_state.step = 1
                    st.rerun()

        # 변환 탭 내 아크 생성 (컨셉이 세팅된 후)
        if st.session_state.concept and st.session_state.step >= 1 and not st.session_state.arc:
            st.markdown("---")
            st.markdown('<div class="section-header">📊 시즌 아크 설계 <span class="en">STEP 2 · SEASON ARC</span></div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="callout"><div class="cl">컨셉 확인</div>'
                f'{st.session_state.concept.get("title","")} — {st.session_state.concept.get("logline","")}</div>',
                unsafe_allow_html=True
            )
            if st.button("📊 100화 아크 + 도파민 마일스톤 생성 (4회 분할)", type="primary", use_container_width=True, key="cv_arc"):
                total = st.session_state.concept.get("total_eps",100)
                arc_progress = st.empty()
                result = generate_arc_chunks(
                    st.session_state.concept, total,
                    st.session_state.producer_note, arc_progress)
                if result:
                    st.session_state.arc = result
                    st.session_state.step = 2
                    st.rerun()

        if st.session_state.arc:
            st.markdown("---")
            st.markdown(
                '<div style="background:var(--g);color:white;padding:1rem 1.5rem;border-radius:8px;'
                'text-align:center;margin:1rem 0">'
                '<div style="font-size:1.1rem;font-weight:800;margin-bottom:.3rem">✅ 아크 생성 완료!</div>'
                '<div style="font-size:.85rem;opacity:.9">위의 <b>✍️ 새 숏폼 만들기</b> 탭을 클릭하면 STEP 3 블록 집필이 바로 시작됩니다.</div>'
                '<div style="font-size:2rem;margin-top:.5rem">↑</div>'
                '</div>', unsafe_allow_html=True
            )

st.markdown(
    '<div style="text-align:center;font-size:.62rem;padding:30px 0 16px;letter-spacing:2px;opacity:.2;">'
    '© 2026 BLUE JEANS PICTURES · Shortform Engine v2.8 · Opus(집필) + Sonnet(설계)'
    '</div>', unsafe_allow_html=True
)
