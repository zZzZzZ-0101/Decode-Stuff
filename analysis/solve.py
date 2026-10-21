"""《叠浪淘沙 · 璇玑秋声》完整求解：卷面 + 《四处补遗》 → 明文音节序列。

步骤：
  1. 种子 = 题引 56 字笔画；sbox 取"次数降序、同次数值升序"；56 长状态展卷 115 转得轮钥。
  2. 230 实字连续两两配对，rk[i][0] 奇偶定正切 / 倒切，得 115 个密文音节。
  3. 语境子环 + 三相环序 + 前位明文回声，逆序施行，解出 115 个"织后"音节。
  4. 织位（回文）：明文逐行写入 23 行 × 5 列的网格（即正文 23 行、每行 5 对），
     加密顺序沿"回"字形螺旋读取该网格；解密后按螺旋位置回填，再逐行读出即为明文。
音节表：GB2312 6763 字的 pypinyin 首读音（strict 声韵，零声母排最前，不收空韵母、不收轻声）。
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "h30_decrypt"))
from pypinyin import pinyin, Style
from pypinyin.contrib.tone_convert import to_initials, to_finals
from spec import round_keys, make_sbox, cipher_syllables, Rings, decrypt, encrypt
from legal import GB

ROWS, COLS = 23, 5          # 正文 23 行 × 每行 5 对


def build_table():
    tab = {}
    for ch in GB:
        t = pinyin(ch, style=Style.TONE3)[0][0]
        if t[-1] in "1234":
            f = to_finals(t, strict=True)
            if f:
                tab[(to_initials(t, strict=True), f, int(t[-1]))] = t
    return tab


def spiral_order(rows, cols):
    """"回"字形螺旋：从右上角出发，先沿最右一列向下，再沿末行向左、首列向上、首行向右，逐圈内收。
    返回网格格子的行优先编号序列。"""
    dirs = [(1, 0), (0, -1), (-1, 0), (0, 1)]          # 下、左、上、右（逆时针）
    r, c, d = 0, cols - 1, 0
    seen, out = set(), []
    for _ in range(rows * cols):
        out.append(r * cols + c); seen.add((r, c))
        nr, nc = r + dirs[d][0], c + dirs[d][1]
        if not (0 <= nr < rows and 0 <= nc < cols) or (nr, nc) in seen:
            d = (d + 1) % 4
            nr, nc = r + dirs[d][0], c + dirs[d][1]
        r, c = nr, nc
    return out


def solve():
    tab = build_table()
    R = Rings(sorted({a for a, _, _ in tab}), sorted({b for _, b, _ in tab}), set(tab))
    rk = round_keys(make_sbox(True, True, "A"))
    cs = cipher_syllables(rk)
    assert all(c in tab for c in cs), "正倒后存在非法密文音节"
    woven = decrypt(cs, rk, R)
    assert encrypt(woven, rk, R) == cs, "重新加密未能复现密文"
    order = spiral_order(ROWS, COLS)            # 第 j 轮加密的是网格第 order[j] 格
    assert sorted(order) == list(range(ROWS * COLS))
    plain = [None] * (ROWS * COLS)
    for j, cell in enumerate(order):
        plain[cell] = woven[j]
    return [tab[x] for x in plain], [tab[x] for x in woven]


if __name__ == "__main__":
    plain, woven = solve()
    print("明文音节（%d）：" % len(plain))
    for r in range(ROWS):
        print("  ", " ".join(plain[r * COLS:(r + 1) * COLS]))
