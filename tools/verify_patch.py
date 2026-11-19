"""Shortform Engine 프롬프트 점검 도구.

1) 기본 점검 (API 키 없이 실행):
       python tools/verify_patch.py
   모든 공식 × 톤 × 자막 형식 조합으로 프롬프트를 만들어 보고
   - 특정 작품의 이름·설정이 남아 있지 않은지
   - 다른 공식의 예시가 섞여 들어가지 않는지
   - 조용한 악역 지침이 조용한 톤에서만 들어가는지
   - 자막 형식이 선택대로 들어가는지
   를 확인한다.

2) 실제 집필 점검 (API 키 필요, 비용 발생):
       ANTHROPIC_API_KEY=sk-ant-... python tools/verify_patch.py --live 재벌복수 능력각성
   공식마다 컨셉 → 아크(EP1~25) → 블록1(EP1~5)을 실제로 뽑아
   tools/live_out/ 에 저장하고, 금지어가 나왔는지 알려 준다.
   톤과 자막 형식을 바꾸려면 --tone quiet / --subtitle sentence 를 붙인다.
   주인공 향과 과금 관문은 --lead male / --paywall 8 로 바꾼다.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import prompt as P  # noqa: E402

# 예전 프롬프트에 박혀 있던 작품 고유 낱말
BANNED = ["세영", "도균", "오진혁", "대성그룹", "대성", "기획안", "강태오", "김이슬",
          "한성건설", "수민", "지수", "인턴", "감상문"]

DUMMY_CONCEPT = {
    "title": "점검용", "logline": "점검용 로그라인", "season_question": "점검용 질문",
    "market": "글로벌", "rating": "teen",
    "protagonist": {"name": "가나", "age": "29"}, "villain": {"name": "다라", "age": "55"},
    "helper": {"name": "마바"}, "rival": {"name": "사아"},
    "supporting_cast": [{"name": "자차", "function": "A분노유발"}],
    "dopamine_design": {}, "paywall_design": {},
    "location_design": {"main_locations": [{"name": "점검용 장소"}], "sub_locations": []},
}
DUMMY_BLOCK = {"ep_range": "EP 1~5", "phase": "도입", "theme": "점검", "episodes": [
    {"ep": i, "summary": "점검", "emotion_mode": m, "cliffhanger_type": "Slap",
     "cliffhanger": "점검", "first_subtitle": "", "paywall": False}
    for i, m in enumerate(["굴욕", "분노", "굴욕", "통쾌", "긴장"], start=1)]}


def all_prompts(formula, tone, sub, lead="female", pw=10):
    concept = dict(DUMMY_CONCEPT, formula=formula)
    kw = dict(lead=lead, paywall_ep=pw)
    modes = ["굴욕", "분노", "굴욕", "통쾌", "긴장"]
    return {
        "system": P.build_system_prompt(formula, tone, sub, **kw),
        "concept": P.build_concept_prompt(formula, "주인공 입력", "악역 입력", "비밀", "질문",
                                          market="글로벌", tone=tone, subtitle_style=sub, **kw),
        "arc1": P.build_arc_prompt(concept, chunk=1, subtitle_style=sub, **kw),
        "arc3": P.build_arc_prompt(concept, chunk=3, subtitle_style=sub, **kw),
        "block1": P.build_block_prompt(concept, DUMMY_BLOCK, 1, emotional_modes=modes,
                                       tone=tone, subtitle_style=sub, **kw),
        "block2": P.build_block_prompt(concept, dict(DUMMY_BLOCK, ep_range="EP 6~10", episodes=[
            dict(e, ep=e["ep"] + 5) for e in DUMMY_BLOCK["episodes"]]), 2, emotional_modes=modes,
                                       tone=tone, subtitle_style=sub, **kw),
        "block7": P.build_block_prompt(concept, dict(DUMMY_BLOCK, ep_range="EP 31~35"), 7,
                                       emotional_modes=["연민", "절망", "공감", "유혹", "미련"],
                                       tone=tone, subtitle_style=sub, **kw),
        "convert": P.build_convert_prompt("원본 글", formula, market="글로벌", tone=tone, subtitle_style=sub, **kw),
        "pilot": P.build_pilot_prompt({}, market="글로벌", formula_key=formula, tone=tone, subtitle_style=sub, **kw),
    }


def static_check():
    fails = []
    formulas = list(P.MAKJANG_FORMULAS.keys()) + ["없는공식"]
    # 공식마다 그 공식의 교정 예시에만 나오는 줄 (S# 헤더 다음 줄)
    sig = {k: {t: v["scene"][t].split("\n")[1] for t in P.TONE_RULES}
           for k, v in P.FORMULA_EXAMPLES.items()}
    n = 0
    combos = [(f, tone, sub, lead, pw) for f in formulas for tone in P.TONE_RULES
              for sub in P.SUBTITLE_STYLES for lead in P.LEAD_RULES for pw in P.PAYWALL_OPTIONS]
    for f, tone, sub, lead, pw in combos:
        if True:
            if True:
                n += 1
                tag = f"{f}/{tone}/{sub}/{lead}/{pw}"
                ps = all_prompts(f, tone, sub, lead, pw)
                for name, text in ps.items():
                    for w in BANNED:
                        if w in text:
                            fails.append(f"{tag} {name}: 금지어 '{w}'")
                    if "⟦" in text or "⟧" in text:
                        fails.append(f"{tag} {name}: 과금 관문 표시가 채워지지 않음")
                    if "<<" in text or ">>" in text:
                        fails.append(f"{tag} {name}: 조립 안 된 표시가 남음")
                    if re.search(r"\{[a-z_]+(\[|\.|\})", text):
                        fails.append(f"{tag} {name}: 치환 안 된 변수가 남음")
                sysp = ps["system"]
                own = f if f in P.FORMULA_EXAMPLES else "_공통"
                male_harsh = (lead == "male" and tone == "harsh")
                # 1) 선택한 공식·톤의 예시만 들어갔는가 (남성향+독한 톤은 전용 예시)
                for k in sig:
                    for t in P.TONE_RULES:
                        inside = sig[k][t] in sysp
                        should = (k == own and t == tone and not male_harsh)
                        if male_harsh and t == "harsh":
                            continue  # 남성향 전용 예시는 같은 무대에서 시작할 수 있어 아래 1-1에서 따로 본다
                        if inside != should:
                            fails.append(f"{tag}: 예시 주입 오류 ({k}/{t} 포함={inside})")
                # 1-1) 남성향: 주인공이 맞거나 꿇는 예시가 없어야 한다
                if lead == "male":
                    for name in ("system", "block1", "pilot"):
                        for bad in ("[주인공]의 뺨을 친다", "[주인공]의 뺨을 때", "[주인공]이 무릎을 꿇",
                                    "[주인공]의 어깨를 누른다", "[주인공]을 밀친다", "[주인공]의 어깨를 밀친다",
                                    "[주인공]이 밀려 나온다", "[주인공]이 향로 옆으로 넘어진다"):
                            if bad in ps[name]:
                                fails.append(f"{tag} {name}: 남성향인데 주인공이 당하는 예시 '{bad}'")
                for name in ("system", "block1", "pilot"):
                    if ("주인공 향: 남성향 — 이 작품에만" in ps[name]) != (lead == "male"):
                        fails.append(f"{tag} {name}: 주인공 향 지침 주입 오류")
                # 1-2) 과금 관문 화수가 선택대로 들어갔는가
                if f"EP{pw - 1}~{pw}" not in ps["system"] or f"EP {pw} 이전에도" not in ps["arc1"]:
                    fails.append(f"{tag}: 과금 관문 화수 주입 오류")
                if pw in (8, 10) and "과금 전환점 — EP" not in ps["block2"]:
                    fails.append(f"{tag}: 과금 블록 분량 안내 누락")
                if pw == 16 and "과금 전환점 — EP" in ps["block2"]:
                    fails.append(f"{tag}: 과금 블록이 아닌데 과금 안내가 들어감")
                # 2) 조용한 악역 지침은 조용한 톤에서만
                quiet_mark = "조용한 톤 — 이 작품에만 적용"
                harsh_mark = "독한 톤 — 이 작품에만 적용"
                for name in ("system", "block1", "block7", "pilot", "convert"):
                    if (quiet_mark in ps[name]) != (tone == "quiet"):
                        fails.append(f"{tag} {name}: 조용한 톤 지침 주입 오류")
                    if (harsh_mark in ps[name]) != (tone == "harsh"):
                        fails.append(f"{tag} {name}: 독한 톤 지침 주입 오류")
                    if tone == "harsh" and "웃으면서 말한다" in ps[name]:
                        fails.append(f"{tag} {name}: 독한 톤에 조용한 악역 문구")
                # 3) 자막 형식
                badge = "[충격/반전/사이다]"
                for name in ("system", "block1", "block7", "pilot"):
                    has_badge = badge in ps[name]
                    if has_badge != (sub == "badge"):
                        fails.append(f"{tag} {name}: 자막 형식 주입 오류 (배지 문구 포함={has_badge})")
                    if "[자막]" not in ps[name]:
                        fails.append(f"{tag} {name}: [자막] 줄이 포맷에서 사라짐")
                # 4) EP1 기준은 EP1을 쓰는 곳에만
                if "EP1 전용 기준 — 5개 모두" not in ps["block1"] or "EP1 전용 기준 — 5개 모두" not in ps["pilot"]:
                    fails.append(f"{tag}: EP1 기준 누락")
                if "EP1 전용 기준 — 5개 모두" in ps["block7"]:
                    fails.append(f"{tag}: EP1 기준이 다른 블록에 들어감")
                # 5) 작은 응징·혼자 씬 한도
                if "작은 응징 규칙" not in ps["arc1"]:
                    fails.append(f"{tag}: 아크에 작은 응징 규칙 누락")
                if "전체의 10% 이하" not in ps["block1"]:
                    fails.append(f"{tag}: 혼자 씬 한도 누락")
    # arc_hint에 작은 응징이 들어 있는가
    for k, v in P.MAKJANG_FORMULAS.items():
        if "작은 응징" not in v["arc_hint"]:
            fails.append(f"{k}: arc_hint에 작은 응징 없음")
    # 감정 모드 예시에 금지어가 없는가
    for k, v in P.EMOTIONAL_MODES.items():
        for w in BANNED:
            if any(w in str(x) for x in v.values()):
                fails.append(f"감정 모드 {k}: 금지어 '{w}'")
    print(f"조합 {n}개 × 프롬프트 9종 점검")
    if fails:
        print(f"실패 {len(fails)}건")
        for x in fails[:40]:
            print(" -", x)
        return 1
    print("전부 통과")
    return 0


def live_check(formulas, tone, sub, lead="female", pw=10):
    import anthropic
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        print("ANTHROPIC_API_KEY 환경변수가 없습니다.")
        return 1
    client = anthropic.Anthropic(api_key=key)
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_out")
    os.makedirs(out_dir, exist_ok=True)

    def ask(prompt, model, max_tokens):
        r = client.messages.create(model=model, max_tokens=max_tokens,
                                   messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in r.content if hasattr(b, "text")).strip()

    def to_json(text):
        text = re.sub(r"```json\s*|```\s*", "", text).strip()
        return json.loads(text[text.find("{"): text.rfind("}") + 1])

    # 일부러 직장이 아닌, 설정이 비어 있는 입력을 준다. 무대는 엔진이 고르게 둔다.
    rc = 0
    for f in formulas:
        print(f"[{f}] 컨셉 생성 중...")
        concept = to_json(ask(P.build_concept_prompt(
            f, "이름과 직업은 자유. 가진 것 없이 무시당하는 사람.", "이름과 직업은 자유. 주인공을 짓밟는 사람.",
            "자동 생성", "주인공은 빼앗긴 것을 되찾을 수 있을까", tone=tone, subtitle_style=sub,
            lead=lead, paywall_ep=pw),
            P.MODEL_PLAN, 6000))
        print(f"[{f}] 아크(EP1~25) 생성 중...")
        arc = to_json(ask(P.build_arc_prompt(concept, chunk=1, subtitle_style=sub, lead=lead, paywall_ep=pw),
                          P.MODEL_PLAN, 12000))
        blk = arc["blocks"][0]
        modes = [e.get("emotion_mode", "") for e in blk.get("episodes", [])]
        print(f"[{f}] 블록1(EP1~5) 집필 중...")
        script = ask(P.build_block_prompt(concept, blk, 1, emotional_modes=modes,
                                          tone=tone, subtitle_style=sub, lead=lead, paywall_ep=pw),
                     P.MODEL_WRITE, 12000)
        base = os.path.join(out_dir, f"{f}_{tone}_{sub}")
        json.dump({"concept": concept, "arc_chunk1": arc}, open(base + ".json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        open(base + "_EP1-5.txt", "w", encoding="utf-8").write(script)
        hits = [w for w in BANNED if w in script or w in json.dumps(concept, ensure_ascii=False)]
        ph = re.findall(r"\[(?:주인공|악역|상대역|조력자|감초|강자|아이)\]", script)
        subs = [ln for ln in script.splitlines() if ln.strip().startswith("[자막]")]
        payback = [e["ep"] for b in arc["blocks"][:3] for e in b["episodes"]
                   if e.get("emotion_mode") in ("통쾌", "짜릿", "복수", "카타르시스")]
        print(f"[{f}] 저장: {base}_EP1-5.txt")
        print(f"   금지어: {hits or '없음'} / 자리표시가 대본에 남음: {len(ph)}곳 / [자막] 줄: {len(subs)}개")
        print(f"   EP1~15 응징 화: {payback}")
        if hits or ph or len(subs) != 5:
            rc = 1
    return rc


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--live" in args:
        tone = args[args.index("--tone") + 1] if "--tone" in args else P.DEFAULT_TONE
        sub = args[args.index("--subtitle") + 1] if "--subtitle" in args else P.DEFAULT_SUBTITLE
        names = [a for a in args if a in P.MAKJANG_FORMULAS] or ["재벌복수", "능력각성"]
        lead = args[args.index("--lead") + 1] if "--lead" in args else P.DEFAULT_LEAD
        pw = int(args[args.index("--paywall") + 1]) if "--paywall" in args else P.DEFAULT_PAYWALL
        sys.exit(live_check(names, tone, sub, lead, pw))
    sys.exit(static_check())
