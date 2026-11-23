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


def all_prompts(formula, tone, sub, lead="female", pw=10, ai=False):
    concept = dict(DUMMY_CONCEPT, formula=formula)
    kw = dict(lead=lead, paywall_ep=pw, ai_mode=ai)
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
    combos = [(f, tone, sub, lead, pw, ai) for f in formulas for tone in P.TONE_RULES
              for sub in P.SUBTITLE_STYLES for lead in P.LEAD_RULES for pw in P.PAYWALL_OPTIONS
              for ai in (False, True)]
    for f, tone, sub, lead, pw, ai in combos:
        if True:
            if True:
                n += 1
                tag = f"{f}/{tone}/{sub}/{lead}/{pw}/{'ai' if ai else 'x'}"
                ps = all_prompts(f, tone, sub, lead, pw, ai)
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
                if pw == 5 and "과금 전환점 — EP" not in ps["block1"]:
                    fails.append(f"{tag}: 무료 5화형인데 블록1에 과금 안내 누락")
                # 1-3) AI 제작 모드 지침은 켰을 때만
                for name in ("system", "block1", "block7", "pilot"):
                    if ("AI 제작 모드 — 이 대본은" in ps[name]) != ai:
                        fails.append(f"{tag} {name}: AI 제작 모드 지침 주입 오류")
                if ("AI 제작 모드 — 컨셉 설계 제약" in ps["concept"]) != ai:
                    fails.append(f"{tag}: 컨셉의 AI 제작 모드 제약 주입 오류")
                if ai and "supporting_cast 최소 3명" in ps["concept"]:
                    fails.append(f"{tag}: AI 제작 모드인데 '감초 최소 3명' 규칙이 남음")
                # 1-4) 매 화 반전, 타겟
                if "반전 1번 이상" not in ps["system"] or "매 화 반전" not in ps["arc1"]:
                    fails.append(f"{tag}: 매 화 반전 규칙 누락")
                for name in ("concept", "arc1", "block1", "pilot"):
                    if "[타겟: " not in ps[name]:
                        fails.append(f"{tag} {name}: 타겟 누락")
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
                if "EP1 전용 기준 — 6개 모두" not in ps["block1"] or "EP1 전용 기준 — 6개 모두" not in ps["pilot"]:
                    fails.append(f"{tag}: EP1 기준 누락")
                for old in ("거부당하는 그림", "강자의 얼굴", "타격 대사"):
                    if old in ps["block1"] or old in ps["pilot"] or old in ps["arc1"]:
                        fails.append(f"{tag}: 예전 EP1 기준 문구 '{old}'가 남음")
                if "EP1 전용 기준 — 6개 모두" in ps["block7"]:
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
    # 총 화수별 아크: 청크 수, 블록 수, 마지막 화
    for total in (20, 30, 50, 80, 90, 100):
        for pw in (5, 10, 16):
            if pw > total - 3:
                continue
            concept = dict(DUMMY_CONCEPT, formula="복수극", total_eps=total)
            chunks = -(-total // 25)
            seen = 0
            for ch in range(1, chunks + 1):
                a = P.build_arc_prompt(concept, total, chunk=ch, total_chunks=chunks, paywall_ep=pw)
                import re as _re
                if "⟦" in a or _re.search(r"EP 6~[1-5](?!\d)", a):
                    fails.append(f"아크 {total}화/관문{pw}/청크{ch}: 화수 표기 오류")
                m = _re.search(r"blocks 정확히 (\d+)개", a)
                seen += int(m.group(1)) if m else 0
            if seen != -(-total // 5):
                fails.append(f"아크 {total}화: 블록 수 합계 {seen} (기대 {-(-total // 5)})")
            last = P.build_arc_prompt(concept, total, chunk=chunks, total_chunks=chunks, paywall_ep=pw)
            if f"EP {total}이 이 작품의 마지막 화" not in last:
                fails.append(f"아크 {total}화: 마지막 화 안내 누락")
    # 자동 점검기: 실제 불합격 원고와 합격 예시
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
    bad = open(os.path.join(base, "danjjan_ep1-5_v21.txt"), encoding="utf-8").read()
    r = P.check_script(bad, {"protagonist": {"name": "한세영"}, "villain": {"name": "오진혁"}, "helper": {"name": "윤수민"}})
    joined = " ".join(r["issues"])
    for need in ("EP 2: 대사가 0줄", "화면 인서트", "혼자인 씬"):
        if need not in joined:
            fails.append(f"자동 점검기: 예전 불합격 원고에서 '{need}'를 못 잡음")
    good = open(os.path.join(base, "good_three_women.txt"), encoding="utf-8").read()
    r = P.check_script(good, {"protagonist": {"name": "윤서연"}, "villain": {"name": "강해수"}}, ai_mode=True)
    if not r["ok"]:
        fails.append(f"자동 점검기: 합격 예시를 불합격 처리함 {r['issues']}")
    # v3.3: 분량 하한, 주인공 무대사, 최종화, 아크 자막·클리프행어 중복
    cc = {"protagonist": {"name": "윤서연"}, "villain": {"name": "강해수"}, "total_eps": 5}
    thin = ("EP 5 | 🕊️ 해방 | D9\n[자막] \"[사이다] 끝\"\n\nS#1. 본가 — 식탁. 낮.\n"
            "옥분이 서류를 놓는다. 해수가 앉던 의자는 비어 있다.\n\n"
            + "\n".join(["옥분  이 집은 네 거다.", "서연  네.", "옥분  밥 먹자."] * 3)
            + "\n\n서연이 주방으로 걸어간다.")
    joined = " ".join(P.check_script(thin, cc)["issues"])
    for need in ("최종화 분량 하한 700자", "주적(강해수)의 대사가 없습니다"):
        if need not in joined:
            fails.append(f"자동 점검기(v3.3): 얇은 최종화에서 '{need}'를 못 잡음")
    mute = thin.replace("서연  네.", "옥분  그래.")
    mj = " ".join(P.check_script(mute, cc)["issues"])
    if "주인공의 대사가 한 줄도 없습니다" not in mj or "지문으로만 끝납니다" not in mj:
        fails.append("자동 점검기(v3.3): 주인공 대사 0줄 / 지문으로만 끝나는 최종화를 못 잡음")
    prior = [{"ep": 38, "first_subtitle": "[사이다] 미령 무릎", "cliffhanger": "미령, 처음으로 무릎 꿇음"}]
    blk = [{"block_no": 19, "phase": "몰락", "episodes": [
        {"ep": 93, "summary": "시어머니가 위조 선언", "first_subtitle": "[사이다] 미령 무릎", "cliffhanger": "미령, 처음으로 무릎 꿇음"}]}]
    ai = " ".join(P.check_arc_chunk(blk, [], prior))
    if "EP93의 자막이 EP38과 같다" not in ai or "EP93의 클리프행어가 EP38과 같다" not in ai:
        fails.append("아크 점검(v3.3): 앞 청크와 같은 자막·클리프행어를 못 잡음")
    fin_c = dict(DUMMY_CONCEPT, formula="복수극", total_eps=100)
    fin_b = {"ep_range": "EP 96~100", "episodes": [{"ep": n, "summary": "x"} for n in range(96, 101)]}
    if "최종화 — EP 100" not in P.build_block_prompt(fin_c, fin_b, 20):
        fails.append("블록 프롬프트(v3.3): 최종화 블록에 최종화 기준이 없음")
    if "최종화 — EP" in P.build_block_prompt(fin_c, dict(fin_b, ep_range="EP 91~95",
            episodes=[{"ep": n, "summary": "x"} for n in range(91, 96)]), 19):
        fails.append("블록 프롬프트(v3.3): 최종화가 아닌 블록에 최종화 기준이 들어감")
    print(f"조합 {n}개 × 프롬프트 9종 점검 + 화수별 아크 + 자동 점검기")
    if fails:
        print(f"실패 {len(fails)}건")
        for x in fails[:40]:
            print(" -", x)
        return 1
    print("전부 통과")
    return 0


def live_check(formulas, tone, sub, lead="female", pw=10):
    # 참고: 실제 집필 확인은 배포된 앱에서 하는 편이 쉽다. 이 함수는 로컬에서 키가 있을 때만 쓴다.
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
