"""行内相邻反切对检验。

每行 10 字（左句 5 字 + 右句 5 字，去"兮"）按 (1,2)(3,4)(5,6)(7,8)(9,10) 两两成对，
取上字声母 + 下字韵母，判断是否为合法普通话音节；与随机打乱基线、错位相位对照。
输出：合法数、基线均值/标准差/最大值、z 值，以及 115 个音节的明细表。
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collections import Counter
from pypinyin import pinyin, Style
from data import CLAUSES, TEXT, PY
from legal import GB, is_legal

random.seed(20261021)
TRIALS = 2000


def s21(c):
    """S21 口径：pypinyin strict 声母/韵母（y、w 归零声母，韵母含介音）"""
    return (pinyin(c, style=Style.INITIALS, strict=True)[0][0],
            pinyin(c, style=Style.FINALS, strict=True)[0][0])


LEGAL21 = {s21(ch) for ch in GB}


def legal21(a, b):
    return (s21(a)[0], s21(b)[1]) in LEGAL21


def legal23(a, b):
    return is_legal(PY[a][0], PY[b][1])


def score(seq, phase, fn):
    return sum(fn(seq[i], seq[i + 1]) for i in range(phase, len(seq) - 1, 2))


def main():
    print("口径  相位  合法/总对数  基线均值  标准差  基线最大  z")
    for name, fn in (("S23", legal23), ("S21", legal21)):
        for phase in (0, 1):
            n = len(range(phase, len(TEXT) - 1, 2))
            obs = score(TEXT, phase, fn)
            chars, base = list(TEXT), []
            for _ in range(TRIALS):
                random.shuffle(chars)
                base.append(score(chars, phase, fn))
            m = sum(base) / TRIALS
            sd = (sum((x - m) ** 2 for x in base) / TRIALS) ** 0.5
            print(f"{name}   {phase}     {obs}/{n}      {m:6.1f}   {sd:4.1f}    {max(base)}     {(obs - m) / sd:4.1f}")

    print("\n115 个反切音节（相位 0；上字声母 + 下字韵母，S21 口径；✗ = 两种口径均不合法，△ = 仅 S21 不合法）")
    lines = ["".join(CLAUSES[2 * r:2 * r + 2]) for r in range(23)]
    syllables = []
    for r, ln in enumerate(lines, 1):
        cells = []
        for k in range(5):
            a, b = ln[2 * k], ln[2 * k + 1]
            ini, fin = s21(a)[0], s21(b)[1]
            ok21, ok23 = legal21(a, b), legal23(a, b)
            mark = "" if ok21 else ("✗" if not ok23 else "△")
            cells.append(f"{a}{b} {ini or '∅'}+{fin}{mark}")
            syllables.append((ini, fin))
        print(f"{r:>2} | " + " | ".join(cells))
    print("\n高频音节：", Counter(f"{i or '∅'}+{f}" for i, f in syllables).most_common(8))


if __name__ == "__main__":
    main()
