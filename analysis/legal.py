# 合法普通话音节表（取 GB2312 常用字 6763 的全部读音），两种声韵切分口径
from pypinyin import pinyin, Style
from data import INITIALS

def _gb_chars():
    out = []
    for b1 in range(0xB0, 0xF8):
        for b2 in range(0xA1, 0xFF):
            try: out.append(bytes([b1, b2]).decode('gb2312'))
            except UnicodeDecodeError: pass
    return out
GB = _gb_chars()

def split23(s):
    """S23 口径：按字面拼写切，y w 视作声母，零声母为 ''"""
    for i in sorted(INITIALS, key=len, reverse=True):
        if s.startswith(i): return i, s[len(i):]
    return '', s

LEGAL_TONED = set()     # ('lu', 4)
for ch in GB:
    for p in pinyin(ch, style=Style.TONE3, heteronym=True, neutral_tone_with_five=True)[0]:
        if p[-1].isdigit():
            LEGAL_TONED.add((p[:-1], int(p[-1])))
LEGAL_TONELESS = {s for s, t in LEGAL_TONED}
LEGAL_IF23 = {split23(s) for s in LEGAL_TONELESS}       # 合法 (声母,韵母) 对，S23 口径
I23 = sorted({i for i, f in LEGAL_IF23}, key=lambda x: (INITIALS + [''] ).index(x))
F23 = sorted({f for i, f in LEGAL_IF23})

def is_legal(ini, fin, tone=None):
    s = ini + fin
    if tone is None: return s in LEGAL_TONELESS
    return (s, tone) in LEGAL_TONED
