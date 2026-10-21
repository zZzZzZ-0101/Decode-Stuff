"""按《四处补遗》实现：密钥展开（展卷）、正倒（切）、语境子环与回声（归）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import TIYIN, CLAUSES
from strokes import STROKES

SEED = [STROKES[c] for c in "".join(TIYIN)]          # 56 个笔画值
REAL = "".join(CLAUSES)                               # 230 实字
M, SZ, ROUNDS = 17, 56, 115


def make_sbox(cnt_desc=True, val_asc=True, mode="A"):
    cnt = {v: SEED.count(v) for v in range(1, 18)}
    order = sorted(range(1, 18), key=lambda v: ((-cnt[v]) if cnt_desc else cnt[v], v if val_asc else -v))
    pos = {v: k for k, v in enumerate(order)}
    if mode == "A":   # 参数 x 视作 v-1（与 S=(v-1) mod 17 同空间）
        return [pos[x + 1] for x in range(17)]
    if mode == "B":   # 参数 x 视作 v mod 17（0 ↔ 17）
        return [pos[x if x else 17] for x in range(17)]
    if mode == "D":   # 字面列表 sbox[val]，sbox[0] 未赋值 = 0
        lst = [0] * 18
        for v, k in pos.items(): lst[v] = k
        return lst[:17]


def round_keys(sbox):
    S = [(v - 1) % M for v in SEED]
    rks = []
    for i in range(ROUNDS):
        a = [sbox[(S[j] + i) % M] for j in range(SZ)]
        b = [(a[j] + a[(j + 1) % SZ] + a[(j + 7) % SZ]) % M for j in range(SZ)]
        r = (b[0] + b[7] + b[8]) % SZ
        S = b[r:] + b[:r]
        rks.append((S[i % SZ] + 1, S[(7 * i + 8) % SZ] + 1, S[(8 * i + 7) % SZ] + 1))
    return rks


# ---------------- 音节表与解密 ----------------
from pypinyin import pinyin, Style


def syll(c, strict=True, reading=0):
    """取默认（首）读音的 (声母, 韵母, 声调)；不用多音字列表，避免零声母被丢弃"""
    t = pinyin(c, style=Style.TONE3, neutral_tone_with_five=True)[0][0]
    i = pinyin(c, style=Style.INITIALS, strict=strict)[0][0]
    f = pinyin(c, style=Style.FINALS, strict=strict)[0][0]
    return i, f, int(t[-1]) if t[-1].isdigit() else 5


def build_tables(chars, heteronym=False, strict=True):
    legal = set()
    for ch in chars:
        I = pinyin(ch, style=Style.INITIALS, strict=strict, heteronym=heteronym)[0]
        F = pinyin(ch, style=Style.FINALS, strict=strict, heteronym=heteronym)[0]
        T = pinyin(ch, style=Style.TONE3, neutral_tone_with_five=True, heteronym=heteronym)[0]
        for a, b, t in zip(I, F, T):
            if t[-1] in "1234" and b:
                legal.add((a, b, int(t[-1])))
    INI = sorted({a for a, _, _ in legal})
    FIN = sorted({b for _, b, _ in legal})
    return INI, FIN, legal


class Rings:
    def __init__(self, INI, FIN, legal):
        self.INI, self.FIN, self.legal = INI, FIN, legal

    def ini_ring(self, F, T): return [i for i in self.INI if (i, F, T) in self.legal]
    def fin_ring(self, I, T): return [f for f in self.FIN if (I, f, T) in self.legal]
    def tone_ring(self, I, F): return [t for t in (1, 2, 3, 4) if (I, F, t) in self.legal]

    @staticmethod
    def shift(ring, x, k):
        return ring[(ring.index(x) + k) % len(ring)]


ORDER = {0: "TFI", 1: "ITF", 2: "FIT"}   # 加密时的施行顺序


def decrypt(cipher, rks, R, first_echo=(3, 3, 6)):
    """cipher: 按轮次排列的密文音节 [(I,F,T)]；返回明文音节列表"""
    out = []
    for i, (I, F, T) in enumerate(cipher):
        if i == 0:
            eI, eF, eT = first_echo
        else:
            pi, pf, pt = out[-1]
            eI, eF, eT = R.FIN.index(pf), pt, R.INI.index(pi)
        k = {"I": rks[i][0] + eI, "F": rks[i][1] + eF, "T": rks[i][2] + eT}
        for comp in reversed(ORDER[i % 3]):
            if comp == "I": I = R.shift(R.ini_ring(F, T), I, -k["I"])
            elif comp == "F": F = R.shift(R.fin_ring(I, T), F, -k["F"])
            else: T = R.shift(R.tone_ring(I, F), T, -k["T"])
        out.append((I, F, T))
    return out


def encrypt(plain, rks, R, first_echo=(3, 3, 6)):
    out = []
    for i, (I, F, T) in enumerate(plain):
        if i == 0:
            eI, eF, eT = first_echo
        else:
            pi, pf, pt = plain[i - 1]
            eI, eF, eT = R.FIN.index(pf), pt, R.INI.index(pi)
        k = {"I": rks[i][0] + eI, "F": rks[i][1] + eF, "T": rks[i][2] + eT}
        for comp in ORDER[i % 3]:
            if comp == "I": I = R.shift(R.ini_ring(F, T), I, k["I"])
            elif comp == "F": F = R.shift(R.fin_ring(I, T), F, k["F"])
            else: T = R.shift(R.tone_ring(I, F), T, k["T"])
        out.append((I, F, T))
    return out


def cipher_syllables(rks, pair_order=None, strict=True):
    pair_order = pair_order or list(range(ROUNDS))
    cs = []
    for i, p in enumerate(pair_order):
        u, l = REAL[2 * p], REAL[2 * p + 1]
        iu, fu, tu = syll(u, strict); il, fl, tl = syll(l, strict)
        cs.append((iu, fl, tl) if rks[i][0] % 2 else (il, fu, tu))
    return cs


def spell(I, F, T):
    """strict 声韵 → 拼写"""
    if I == "":
        if F.startswith("i"): s = ("y" + F[1:]) if len(F) > 1 and F[1] not in "nu" or F in ("iou",) else "y" + F
        elif F.startswith("u"): s = "w" + F[1:] if len(F) > 1 else "wu"
        elif F.startswith("v"): s = "yu" + F[1:]
        else: s = F
        s = {"yi": "yi", "yin": "yin", "ying": "ying", "yiou": "you", "yian": "yan", "yiang": "yang", "yiao": "yao",
             "yie": "ye", "yia": "ya", "yiong": "yong", "wuei": "wei", "wuen": "wen", "wueng": "weng", "wei": "wei"}.get(s, s)
        if F == "i": s = "yi"
        if F == "in": s = "yin"
        if F == "ing": s = "ying"
        if F == "u": s = "wu"
        if F == "uei": s = "wei"
        if F == "uen": s = "wen"
        if F == "iou": s = "you"
    else:
        f = {"iou": "iu", "uei": "ui", "uen": "un"}.get(F, F)
        if I in ("j", "q", "x") and f.startswith("v"): f = "u" + f[1:]
        s = I + f
    return s.replace("v", "ü") + str(T)
