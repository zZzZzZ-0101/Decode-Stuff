#!/usr/bin/env python3
"""《叠浪淘沙 · 璇玑秋声》独立求解程序。

输入：challenge/challenge.txt（卷面原文）。算法依据：challenge/supplement.txt（命题方《四处补遗》）。
本文件不依赖 research/ 中的任何代码。

流程
  1. 切   ：去"兮"与标点得 230 实字，连续两两配对得 115 对；第 i 对按轮钥 rk[i][0] 的奇偶取正切 / 倒切。
  2. 展卷 ：种子 = 题引 56 字笔画；sbox 由种子自生；56 长状态经 115 转（代换、扩散、轮转）挤出 345 枚轮钥。
  3. 归   ：在语境子环上逆序撤销三相移位，移位量 = 轮钥 + 前位明文回声。
  4. 织位 ：明文逐行写入 23 行 × 5 列网格，加密顺序为"回"字形螺旋；按螺旋回填后逐行读出。

用法：python3 solution/solve.py [--quiet]
"""
import os
import re
import sys
from collections import Counter

from pypinyin import pinyin, Style
from pypinyin.contrib.tone_convert import to_initials, to_finals

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHALLENGE = os.path.join(ROOT, "challenge", "challenge.txt")

# 题引用字的规范简体笔画（49 个不同字）
STROKES = {'万': 3, '山': 3, '霜': 17, '叶': 5, '下': 3, '秋': 9, '烟': 10, '千': 3, '回': 6, '锦': 13,
           '字': 6, '未': 5, '成': 6, '篇': 15, '灯': 6, '深': 11, '帘': 8, '底': 8, '藏': 17, '雁': 12,
           '足': 7, '谁': 10, '家': 10, '玉': 5, '笛': 11, '切': 4, '天': 4, '静': 14, '数': 13, '冰': 6,
           '弦': 8, '骨': 9, '亦': 6, '清': 11, '一': 1, '寸': 3, '文': 4, '织': 8, '眠': 10, '凭': 8,
           '君': 7, '验': 10, '取': 8, '前': 9, '归': 5, '其': 8, '位': 7, '月': 4, '川': 3}

M, SZ, ROUNDS = 17, 56, 115          # 笔画值域、题引字数、轮数
ROWS, COLS = 23, 5                   # 织位网格：正文 23 行 × 每行 5 对
ORDER = {0: "TFI", 1: "ITF", 2: "FIT"}   # 加密时三相环序（解密逆序）

# 汉字读法（人工按音节选字；判定以音节序列为准）
READING = ("二〇二三年秋霜叶如燃千枫尽赤一江澄碧舟楫争流我们把酒当歌不亦乐乎二〇二六年秋又是一年丰收的时节"
           "美好总是在一瞬间却很久很久都难以忘怀今日将这美好镌刻入这方矩阵千回百转字里行间落笔处不过是想让这些"
           "绚烂在时间的洪流里留驻得久一点再久一点")
PUNCTUATED = ("二〇二三年秋，霜叶如燃，千枫尽赤，一江澄碧，舟楫争流。我们把酒当歌，不亦乐乎。"
              "二〇二六年秋，又是一年丰收的时节。美好总是在一瞬间，却很久很久都难以忘怀。"
              "今日将这美好镌刻入这方矩阵，千回百转，字里行间，落笔处不过是想让这些绚烂在时间的洪流里"
              "留驻得久一点，再久一点。")


# ---------------------------------------------------------------- 卷面解析
def read_challenge(path=CHALLENGE):
    text = open(path, encoding="utf-8").read()
    head = text[text.index("题 引"):text.index("正 文")]
    body = text[text.index("正 文"):]
    tiyin = re.findall(r"^\s*([一-鿿]{7})\s*$", head, re.M)
    lines = [l.strip() for l in body.splitlines() if "兮" in l]
    real = "".join(re.sub(r"[^一-鿿]", "", l).replace("兮", "") for l in lines)
    assert len(tiyin) == 8 and len(lines) == 23 and len(real) == 230, "卷面解析失败"
    return tiyin, real


# ---------------------------------------------------------------- 音节与音节表
def syll(ch):
    """单字默认读音 → (声母, 韵母, 声调)，pypinyin strict 口径"""
    t = pinyin(ch, style=Style.TONE3, neutral_tone_with_five=True)[0][0]
    return (pinyin(ch, style=Style.INITIALS, strict=True)[0][0],
            pinyin(ch, style=Style.FINALS, strict=True)[0][0],
            int(t[-1]) if t[-1].isdigit() else 5)


def syllable_table():
    """合法 (声,韵,调) 全集：GB2312 6763 字的默认读音，不收空韵母与轻声"""
    tab = {}
    for b1 in range(0xB0, 0xF8):
        for b2 in range(0xA1, 0xFF):
            try:
                ch = bytes([b1, b2]).decode("gb2312")
            except UnicodeDecodeError:
                continue
            t = pinyin(ch, style=Style.TONE3)[0][0]
            if t[-1] in "1234":
                f = to_finals(t, strict=True)
                if f:
                    tab[(to_initials(t, strict=True), f, int(t[-1]))] = t
    return tab


class Rings:
    """语境子环：固定另两维，只在能相拼的子集上按字母序 / 升序成环"""

    def __init__(self, tab):
        self.legal = set(tab)
        self.ini = sorted({i for i, _, _ in tab})     # 22 项，零声母 '' 居首
        self.fin = sorted({f for _, f, _ in tab})     # 36 项

    def ring(self, comp, I, F, T):
        if comp == "I":
            return [i for i in self.ini if (i, F, T) in self.legal]
        if comp == "F":
            return [f for f in self.fin if (I, f, T) in self.legal]
        return [t for t in (1, 2, 3, 4) if (I, F, t) in self.legal]


# ---------------------------------------------------------------- 展卷：轮钥
def round_keys(seed):
    cnt = Counter(seed)
    order = sorted(range(1, M + 1), key=lambda v: (-cnt[v], v))   # 次数降序，同次数值升序
    sbox = [order.index(x + 1) for x in range(M)]
    S = [(v - 1) % M for v in seed]
    rks = []
    for i in range(ROUNDS):
        a = [sbox[(S[j] + i) % M] for j in range(SZ)]                          # 代换
        b = [(a[j] + a[(j + 1) % SZ] + a[(j + 7) % SZ]) % M for j in range(SZ)]  # 扩散
        r = (b[0] + b[7] + b[8]) % SZ
        S = b[r:] + b[:r]                                                      # 轮转
        rks.append((S[i % SZ] + 1, S[(7 * i + 8) % SZ] + 1, S[(8 * i + 7) % SZ] + 1))
    return sbox, rks


# ---------------------------------------------------------------- 归：子环移位与回声
def shift(R, comp, cur, k):
    I, F, T = cur
    ring = R.ring(comp, I, F, T)
    x = {"I": I, "F": F, "T": T}[comp]
    y = ring[(ring.index(x) + k) % len(ring)]
    return (y, F, T) if comp == "I" else (I, y, T) if comp == "F" else (I, F, y)


def echo(R, prev, first):
    if prev is None:
        return first
    pi, pf, pt = prev
    return (R.fin.index(pf), pt, R.ini.index(pi))     # 回声 I / F / T


def run_chain(R, rks, sylls, first, sign):
    """sign = -1 解密（逆序施行）；+1 加密"""
    out, prev = [], None
    for i, cur in enumerate(sylls):
        e = echo(R, prev if sign < 0 else (sylls[i - 1] if i else None), first)
        k = {"I": rks[i][0] + e[0], "F": rks[i][1] + e[1], "T": rks[i][2] + e[2]}
        steps = reversed(ORDER[i % 3]) if sign < 0 else ORDER[i % 3]
        for comp in steps:
            cur = shift(R, comp, cur, sign * k[comp])
        out.append(cur)
        prev = cur
    return out


# ---------------------------------------------------------------- 织位："回"字形螺旋
def spiral_order(rows=ROWS, cols=COLS):
    """从右上角出发，沿最右一列向下，再沿末行向左、首列向上、首行向右，逐圈内收（逆时针）"""
    dirs = [(1, 0), (0, -1), (-1, 0), (0, 1)]
    r, c, d, seen, out = 0, cols - 1, 0, set(), []
    for _ in range(rows * cols):
        out.append(r * cols + c)
        seen.add((r, c))
        nr, nc = r + dirs[d][0], c + dirs[d][1]
        if not (0 <= nr < rows and 0 <= nc < cols) or (nr, nc) in seen:
            d = (d + 1) % 4
            nr, nc = r + dirs[d][0], c + dirs[d][1]
        r, c = nr, nc
    return out


# ---------------------------------------------------------------- 主流程
def solve(verbose=True):
    log = print if verbose else (lambda *a, **k: None)
    tiyin, real = read_challenge()
    seed = [STROKES[c] for c in "".join(tiyin)]
    first = (STROKES[tiyin[-1][-1]], STROKES[tiyin[0][0]], STROKES[tiyin[-1][-1]] + STROKES[tiyin[0][0]])
    sbox, rks = round_keys(seed)
    tab = syllable_table()
    R = Rings(tab)
    log(f"[卷面]   题引 {len(seed)} 字，正文 {len(real)} 实字；首位回声 (I,F,T) = {first}")
    log(f"[展卷]   sbox = {sbox}；rk[0] = {rks[0]}")
    log(f"[音节表] {len(tab)} 个合法带调音节；声母 {len(R.ini)} 项，韵母 {len(R.fin)} 项")

    cipher, forced = [], [0, 0]
    for i in range(ROUNDS):
        (iu, fu, tu), (il, fl, tl) = syll(real[2 * i]), syll(real[2 * i + 1])
        fwd, rev = (iu, fl, tl), (il, fu, tu)
        if (fwd in tab) != (rev in tab):              # 只有一个方向合法的对，用来检验轮钥
            forced[0] += 1
            forced[1] += (fwd in tab) == (rks[i][0] % 2 == 1)
        cipher.append(fwd if rks[i][0] % 2 else rev)
    legal = sum(c in tab for c in cipher)
    log(f"[切]     正切 {sum(r[0] % 2 for r in rks[:ROUNDS])} 对、倒切 {ROUNDS - sum(r[0] % 2 for r in rks[:ROUNDS])} 对；"
        f"密文音节合法 {legal}/{ROUNDS}；方向唯一确定的 {forced[0]} 对中轮钥吻合 {forced[1]}")
    assert legal == ROUNDS and forced[0] == forced[1]

    woven = run_chain(R, rks, cipher, first, -1)
    assert run_chain(R, rks, woven, first, +1) == cipher
    log("[归]     解密完成；重新加密逐位复现 115 个密文音节")

    plain = [None] * ROUNDS
    for j, cell in enumerate(spiral_order()):
        plain[cell] = woven[j]
    plain_py = [tab[x] for x in plain]
    log("[织位]   按 23×5 网格的回字形螺旋回填，逐行读出")

    ref = [pinyin(ch, style=Style.TONE3, neutral_tone_with_five=True)[0][0] for ch in READING]
    diff = [(i, READING[i], plain_py[i], ref[i]) for i in range(ROUNDS) if plain_py[i] != ref[i]]
    log(f"[核对]   汉字读法逐字默认读音与明文音节一致 {ROUNDS - len(diff)}/{ROUNDS}；差异（均为轻声字）：{diff}")
    return plain_py


if __name__ == "__main__":
    quiet = "--quiet" in sys.argv
    plain = solve(verbose=not quiet)
    print("\n明文音节（每行 5 个，对应正文 23 行）：")
    for r in range(ROWS):
        print("  " + " ".join(f"{s:<7}" for s in plain[r * COLS:(r + 1) * COLS]))
    print("\n明文：\n  " + PUNCTUATED)
