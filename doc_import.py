"""문서에서 글자만 뽑아내는 모듈.

기획서·시놉시스·트리트먼트 파일(PDF, DOCX, HWP, HWPX, TXT, MD, JSON)을
받아 본문 글자를 돌려준다. 화면(main.py)이 이 글자를 AI에게 넘겨
컨셉 입력칸에 나눠 담는다.

화면 코드와 분리해 둔 이유: 파일 읽기만 따로 시험할 수 있게 하기 위해서다.
"""
import io
import json
import re
import struct
import zipfile
import zlib

# AI에게 넘기는 글자 수 상한. 넘으면 앞부분과 뒷부분만 남긴다.
MAX_CHARS = 60000

SUPPORTED = ["pdf", "docx", "hwp", "hwpx", "txt", "md", "json"]


class DocImportError(Exception):
    """사용자에게 그대로 보여 줄 수 있는 읽기 실패 사유."""


def _clean(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _decode_text(data):
    for enc in ("utf-8-sig", "utf-16", "cp949", "euc-kr"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return data.decode("utf-8", errors="ignore")


# ── PDF ─────────────────────────────────────────────
def _from_pdf(data):
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise DocImportError("PDF를 읽는 부품(pypdf)이 설치되어 있지 않습니다.") from e
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise DocImportError("암호가 걸린 PDF입니다. 암호를 풀고 다시 올려 주세요.")
        pages = [(p.extract_text() or "") for p in reader.pages]
    except DocImportError:
        raise
    except Exception as e:
        raise DocImportError(f"PDF를 읽지 못했습니다. ({type(e).__name__})") from e
    text = "\n\n".join(pages)
    if len(text.strip()) < 30:
        raise DocImportError(
            "이 PDF에는 글자가 들어 있지 않습니다. 스캔한 그림 PDF로 보입니다. "
            "글자를 복사해 '붙여넣기' 칸에 넣어 주세요.")
    return text


# ── DOCX ────────────────────────────────────────────
def _from_docx(data):
    try:
        import docx
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError as e:
        raise DocImportError("DOCX를 읽는 부품(python-docx)이 설치되어 있지 않습니다.") from e
    try:
        doc = docx.Document(io.BytesIO(data))
    except Exception as e:
        raise DocImportError(f"DOCX를 읽지 못했습니다. ({type(e).__name__})") from e
    out = []
    # 문단과 표를 문서에 놓인 순서대로 읽는다. (기획서는 표가 많다)
    for child in doc.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            out.append(Paragraph(child, doc).text)
        elif tag == "tbl":
            for row in Table(child, doc).rows:
                cells, seen = [], set()
                for c in row.cells:
                    if id(c._tc) in seen:      # 합쳐진 칸은 한 번만
                        continue
                    seen.add(id(c._tc))
                    t = c.text.strip().replace("\n", " / ")
                    if t:
                        cells.append(t)
                if cells:
                    out.append(" | ".join(cells))
    return "\n".join(out)


# ── HWP (한글 5.x) ──────────────────────────────────
_HWP_PARA_TEXT = 67  # HWPTAG_PARA_TEXT
# 뒤에 14글자(28바이트) 딸린 조종 글자들
_HWP_EXT_CTRL = {1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23}
_HWP_INLINE_CTRL = {4, 5, 6, 7, 8, 9, 19, 20}


def _hwp_para_text(payload):
    chars, i, n = [], 0, len(payload)
    while i + 1 < n:
        code = struct.unpack_from("<H", payload, i)[0]
        i += 2
        if code in _HWP_EXT_CTRL or code in _HWP_INLINE_CTRL:
            if code == 9:
                chars.append("\t")
            i += 14   # 조종 글자 본문 12바이트 + 닫는 코드 2바이트
        elif code in (10, 13):
            chars.append("\n")
        elif code < 32:
            continue
        else:
            chars.append(chr(code))
    return "".join(chars)


def _hwp_section_text(raw):
    out, i, n = [], 0, len(raw)
    while i + 4 <= n:
        header = struct.unpack_from("<I", raw, i)[0]
        i += 4
        tag = header & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == 0xFFF:
            if i + 4 > n:
                break
            size = struct.unpack_from("<I", raw, i)[0]
            i += 4
        if tag == _HWP_PARA_TEXT:
            out.append(_hwp_para_text(raw[i:i + size]))
        i += size
    return "\n".join(out)


def _from_hwp(data):
    try:
        import olefile
    except ImportError as e:
        raise DocImportError("HWP를 읽는 부품(olefile)이 설치되어 있지 않습니다.") from e
    if not olefile.isOleFile(io.BytesIO(data)):
        raise DocImportError("한글(HWP) 파일 형식이 아닙니다. 파일이 깨졌는지 확인해 주세요.")
    try:
        ole = olefile.OleFileIO(io.BytesIO(data))
        header = ole.openstream("FileHeader").read()
        flags = struct.unpack_from("<I", header, 36)[0]
        if flags & 0x02:
            raise DocImportError("암호가 걸린 한글 파일입니다. 암호를 풀고 다시 올려 주세요.")
        compressed = bool(flags & 0x01)
        sections = sorted(
            (e for e in ole.listdir() if len(e) == 2 and e[0] == "BodyText"),
            key=lambda e: int(re.sub(r"\D", "", e[1]) or 0))
        parts = []
        for entry in sections:
            raw = ole.openstream(entry).read()
            if compressed:
                raw = zlib.decompress(raw, -15)
            parts.append(_hwp_section_text(raw))
        text = "\n".join(parts)
        if len(text.strip()) < 30 and ole.exists("PrvText"):
            # 본문을 못 읽으면 미리보기 글자라도 쓴다. (앞부분만 들어 있다)
            text = ole.openstream("PrvText").read().decode("utf-16-le", errors="ignore")
    except DocImportError:
        raise
    except Exception as e:
        raise DocImportError(f"한글 파일을 읽지 못했습니다. ({type(e).__name__})") from e
    return text


# ── HWPX (한글 새 형식) ─────────────────────────────
def _from_hwpx(data):
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        raise DocImportError("HWPX 파일 형식이 아닙니다.") from e
    names = sorted(n for n in z.namelist()
                   if re.match(r"Contents/section\d+\.xml$", n))
    if not names:
        raise DocImportError("HWPX 안에서 본문을 찾지 못했습니다.")
    parts = []
    for name in names:
        xml = z.read(name).decode("utf-8", errors="ignore")
        for para in re.findall(r"<hp:p[ >].*?</hp:p>", xml, flags=re.S):
            runs = re.findall(r"<hp:t(?: [^>]*)?>(.*?)</hp:t>", para, flags=re.S)
            line = re.sub(r"<[^>]+>", "", "".join(runs))
            parts.append(line.replace("&lt;", "<").replace("&gt;", ">")
                         .replace("&amp;", "&").replace("&quot;", '"'))
    return "\n".join(parts)


# ── JSON ────────────────────────────────────────────
def _from_json(data):
    raw = _decode_text(data)
    try:
        obj = json.loads(raw)
    except Exception:
        return raw   # JSON이 깨져 있어도 글자는 그대로 넘긴다
    return json.dumps(obj, ensure_ascii=False, indent=1)


_READERS = {
    "pdf": _from_pdf, "docx": _from_docx, "hwp": _from_hwp, "hwpx": _from_hwpx,
    "json": _from_json,
    "txt": lambda d: _decode_text(d), "md": lambda d: _decode_text(d),
}


def trim_for_ai(text, limit=MAX_CHARS):
    """너무 긴 문서는 앞 3/4과 뒤 1/4만 남긴다. (기획 정보는 앞, 결말은 뒤에 있다)"""
    if len(text) <= limit:
        return text, False
    head = int(limit * 0.75)
    tail = limit - head
    return (text[:head] + "\n\n[... 가운데 생략 ...]\n\n" + text[-tail:]), True


def extract_text(filename, data):
    """파일 이름과 내용(바이트)을 받아 {"text", "chars", "trimmed", "kind"}를 돌려준다."""
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if ext == "doc":
        raise DocImportError("옛 워드(.doc) 파일은 읽지 못합니다. .docx나 PDF로 저장해서 올려 주세요.")
    if ext not in _READERS:
        raise DocImportError(
            f"'.{ext}' 파일은 읽지 못합니다. 올릴 수 있는 형식: " + ", ".join(SUPPORTED))
    if not data:
        raise DocImportError("빈 파일입니다.")
    text = _clean(_READERS[ext](data))
    if len(text) < 30:
        raise DocImportError("문서에서 읽을 수 있는 글자가 거의 없습니다.")
    full = len(text)
    text, trimmed = trim_for_ai(text)
    return {"text": text, "chars": full, "trimmed": trimmed, "kind": ext}
