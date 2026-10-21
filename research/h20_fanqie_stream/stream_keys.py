"""在 115 个行内反切音节（上字声母 + 下字韵母 + 下字声调）上检验周期笔画密钥与链式差分。

判据：解出的 115 个音节全部合法（无调；再看带调）。
解耦：密钥周期 p 时，音节按 s mod p 分类，各类独立穷举移位 (sI, sF)，并与随机打乱对照。
"""
import os, sys, random, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pypinyin import pinyin, Style
from data import CLAUSES, TIYIN, PY
from strokes import STROKES
from legal import GB

random.seed(7)
INI_ORDER = "b p m f d t n l g k h j q x zh ch sh r z c s".split() + ['']
FIN_ORDER = ("a o e i u v ai ei ao ou an en ang eng ong er "
             "ia ie iao iou ian in iang ing iong ua uo uai uei uan uen uang ueng ve van vn").split()


def s21(c):
    return (pinyin(c, style=Style.INITIALS, strict=True)[0][0],
            pinyin(c, style=Style.FINALS, strict=True)[0][0])


LEGAL = {s21(ch) for ch in GB}
INI = [i for i in INI_ORDER if any(i == a for a, _ in LEGAL)]
FIN = [f for f in FIN_ORDER if any(f == b for _, b in LEGAL)] + sorted({b for _, b in LEGAL} - set(FIN_ORDER) - {''})
nI, nF = len(INI), len(FIN)

lines = ["".join(CLAUSES[2 * r:2 * r + 2]) for r in range(23)]
PAIRS = [(ln[2 * k], ln[2 * k + 1]) for ln in lines for k in range(5)]


def streams(pairs):
    I = [INI.index(s21(a)[0]) for a, b in pairs]
    F = [FIN.index(s21(b)[1]) if s21(b)[1] in FIN else 0 for a, b in pairs]
    return I, F


def chain(x, n, mode):
    if mode == "none": return x[:]
    if mode == "fwd": return [(x[i] - (x[i - 1] if i else 0)) % n for i in range(len(x))]
    if mode == "bwd": return [(x[i] - (x[i + 1] if i + 1 < len(x) else 0)) % n for i in range(len(x))]
    if mode == "both": return chain(chain(x, n, "bwd"), n, "fwd")


def legal_class(I, F, idx, sI, sF, sign):
    return all((INI[(I[j] - sign * sI) % nI], FIN[(F[j] - sign * sF) % nF]) in LEGAL for j in idx)


def scan(I0, F0, mode, pmax=24):
    """返回每个周期 p 下：存在非零全合法移位的类数"""
    I, F = chain(I0, nI, mode), chain(F0, nF, mode)
    out = {}
    for p in range(1, pmax + 1):
        good = 0
        for r in range(p):
            idx = range(r, 115, p)
            if any(legal_class(I, F, idx, a, b, 1) for a in range(nI) for b in range(nF) if (a, b) != (0, 0)):
                good += 1
        out[p] = good
    return out


def stroke_keys(I0, F0, mode):
    """8 周期，每类只试题引对应句 7 个字的笔画值（I、F 同移 / 只移 I / 只移 F，加或减）"""
    I, F = chain(I0, nI, mode), chain(F0, nF, mode)
    best = []
    for comp in ("IF", "I", "F"):
        for sign in (1, -1):
            hit = 0
            for r in range(8):
                idx = range(r, 115, 8)
                vals = {STROKES[c] for c in TIYIN[r]}
                ok = any(legal_class(I, F, idx, v if "I" in comp else 0, v if "F" in comp else 0, sign) for v in vals)
                hit += ok
            best.append((hit, comp, sign))
    return max(best)


def main():
    I0, F0 = streams(PAIRS)
    print(f"声母表 {nI}，韵母表 {nF}；密文音节合法 {sum((INI[i], FIN[f]) in LEGAL for i, f in zip(I0, F0))}/115")
    for mode in ("none", "fwd", "bwd", "both"):
        real = scan(I0, F0, mode)
        ctrl = []
        for _ in range(5):
            pp = PAIRS[:]; random.shuffle(pp)
            # 对照：打乱上下字后重新配对
            ups = [a for a, b in pp]; los = [b for a, b in pp]; random.shuffle(los)
            ctrl.append(scan(*streams(list(zip(ups, los))), mode, 12))
        sk = stroke_keys(I0, F0, mode)
        print(f"\n链式={mode}  笔画密钥(8 周期，命中类数/8，最好配置)={sk}")
        print("  p : 真实(非零全合法类数/p) | 对照均值")
        for p in range(1, 13):
            c = sum(x[p] for x in ctrl) / len(ctrl)
            print(f"  {p:2d}: {real[p]:2d}/{p:<2d} | {c:4.1f}")
        print("  p=13..24 真实：", {p: f"{real[p]}/{p}" for p in range(13, 25)})


if __name__ == "__main__":
    main()
