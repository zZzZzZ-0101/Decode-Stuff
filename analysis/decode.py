# 根据命题方后续补充说明（《四处补遗》及完整装置规格）复现 115 轮反切与子环解密
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir("/tmp/pylib/pypinyin"):
    sys.path.insert(0, "/tmp/pylib")
else:
    for d in os.listdir("/tmp/pylib") if os.path.isdir("/tmp/pylib") else []:
        sys.path.insert(0, os.path.join("/tmp/pylib", d))

from collections import Counter
from pypinyin import pinyin, Style
from pypinyin.style._utils import get_initials, get_finals
from data import TIYIN, TEXT, STROKES
from legal import GB

# 1. 题引 56 字规范笔画 (1..17)
RAW_SEED = [STROKES[c] for line in TIYIN for c in line]

# 2. 《四处补遗》56 长状态轮密钥生成 (M = 17, SZ = 56)
def build_rk_56():
    cnt = Counter(RAW_SEED)
    order = sorted(range(1, 18), key=lambda v: (-cnt[v], v))
    sbox = [order.index(v + 1) for v in range(17)]
    S = [(v - 1) % 17 for v in RAW_SEED]
    rk_list = []
    for i in range(115):
        a = [sbox[(S[j] + i) % 17] for j in range(56)]
        b = [(a[j] + a[(j + 1) % 56] + a[(j + 7) % 56]) % 17 for j in range(56)]
        r = (b[0] + b[7] + b[8]) % 56
        S = b[r:] + b[:r]
        rk = (
            S[i % 56] + 1,
            S[(7 * i + 8) % 56] + 1,
            S[(8 * i + 7) % 56] + 1,
        )
        rk_list.append(rk)
    return sbox, rk_list

# 3. 字母表与合法子环定义（S21 口径，修正 pypinyin 中 lv/nv 韵母提取）
def parse_py(p):
    t = int(p[-1]) if p[-1].isdigit() else 5
    s = (p[:-1] if p[-1].isdigit() else p).replace("v", "ü")
    ini = get_initials(s, strict=True)
    fin = get_finals(s, strict=True).replace("ü", "v")
    return (ini, fin, t)

def char_syll(ch):
    p = pinyin(ch, style=Style.TONE3)[0][0]
    return parse_py(p)

LEGAL_SYLLS = set()
CHAR_MAP = {}
for ch in GB:
    s = char_syll(ch)
    if s[1] and s[2] in (1, 2, 3, 4):
        LEGAL_SYLLS.add(s)
        CHAR_MAP.setdefault(s, []).append(ch)

INI_ORDER = sorted({i for i, _, _ in LEGAL_SYLLS})
FIN_ORDER = sorted({f for _, f, _ in LEGAL_SYLLS})

def ini_ring(f, t):
    return [ini for ini in INI_ORDER if (ini, f, t) in LEGAL_SYLLS]

def fin_ring(i, t):
    return [fin for fin in FIN_ORDER if (i, fin, t) in LEGAL_SYLLS]

def tone_ring(i, f):
    return [tone for tone in (1, 2, 3, 4) if (i, f, tone) in LEGAL_SYLLS]

def decrypt_56():
    sbox, rk_list = build_rk_56()
    # 【三】「切」：rk[i][0] 为奇正切，为偶倒切
    ct_sylls = []
    for i in range(115):
        u, l = TEXT[2 * i], TEXT[2 * i + 1]
        iu, fu, tu = char_syll(u)
        il, fl, tl = char_syll(l)
        if rk_list[i][0] % 2 == 1:
            ct_sylls.append((iu, fl, tl))
        else:
            ct_sylls.append((il, fu, tu))

    assert all(s in LEGAL_SYLLS for s in ct_sylls), "存在非法反切音节"

    # 【四】【五】「归」：语境子环 + 三相轮转逆序 + 前位明文回声编号
    pts = []
    for i in range(115):
        ic, fc, tc = ct_sylls[i]
        k0, k1, k2 = rk_list[i]
        if i == 0:
            echo_I = RAW_SEED[-1]
            echo_F = RAW_SEED[0]
            echo_T = echo_I + echo_F
        else:
            pi, pf, pt = pts[i - 1]
            echo_I = FIN_ORDER.index(pf)
            echo_F = pt
            echo_T = INI_ORDER.index(pi)

        k_I = k0 + echo_I
        k_F = k1 + echo_F
        k_T = k2 + echo_T

        curr_i, curr_f, curr_t = ic, fc, tc
        if i % 3 == 0:
            steps = ["I", "F", "T"]  # 加密：调->韵->声；解密逆序：声->韵->调
        elif i % 3 == 1:
            steps = ["F", "T", "I"]  # 加密：声->调->韵；解密逆序：韵->调->声
        else:
            steps = ["T", "I", "F"]  # 加密：韵->声->调；解密逆序：调->声->韵

        for st in steps:
            if st == "I":
                ir = ini_ring(curr_f, curr_t)
                curr_i = ir[(ir.index(curr_i) - k_I) % len(ir)]
            elif st == "F":
                fr = fin_ring(curr_i, curr_t)
                curr_f = fr[(fr.index(curr_f) - k_F) % len(fr)]
            elif st == "T":
                tr = tone_ring(curr_i, curr_f)
                curr_t = tr[(tr.index(curr_t) - k_T) % len(tr)]
        pts.append((curr_i, curr_f, curr_t))

    return sbox, rk_list, ct_sylls, pts

if __name__ == "__main__":
    sbox, rk_list, ct_sylls, pts = decrypt_56()
    print(f"RAW_SEED (56): {RAW_SEED}")
    print(f"SBOX (17):     {sbox}")
    print(f"RK[0]:         {rk_list[0]}")
    print(f"反切音节合法率: {sum(s in LEGAL_SYLLS for s in ct_sylls)} / 115\n")
    for i, s in enumerate(pts):
        cands = "".join(CHAR_MAP.get(s, [])[:8])
        print(f"{i:3d}: {s[0]+s[1]+str(s[2]):8s} | {cands}")
