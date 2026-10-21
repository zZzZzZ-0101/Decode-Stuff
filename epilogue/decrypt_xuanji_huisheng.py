#!/usr/bin/env python3
"""《叠浪淘沙 · 璇玑回声》解密：解题方的回信，按《璇玑秋声》同一套规则加密。

与原卷的差别只在参数：题引换成新的 8 句（种子随之改变），正文 29 行，轮数 145，织位网格 29 × 5。
算法部分直接复用 solution/solve.py。

用法：python3 epilogue/decrypt_xuanji_huisheng.py
"""
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("solve", os.path.join(HERE, "..", "solution", "solve.py"))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

# 新题引用字的规范简体笔画（与 hanzi-writer-data 2.0.1 一致；该数据对原卷题引 49 字亦逐字吻合）
STROKES = {'璇': 15, '玑': 6, '一': 1, '卷': 8, '费': 9, '推': 11, '敲': 14, '回': 6, '文': 4, '千': 3,
           '转': 8, '夜': 8, '迢': 8, '切': 4, '开': 4, '霜': 17, '笛': 11, '声': 7, '犹': 7, '在': 6,
           '织': 8, '尽': 6, '冰': 6, '弦': 8, '字': 6, '未': 5, '凋': 10, '溪': 13, '水': 4, '不': 4,
           '留': 10, '秋': 9, '色': 6, '住': 7, '欢': 6, '颜': 15, '长': 4, '伴': 7, '故': 9, '人': 2,
           '遥': 13, '莫': 10, '道': 12, '机': 6, '关': 6, '藏': 17, '得': 11, '巧': 5, '灯': 6, '前': 9,
           '笑': 10, '破': 10, '寒': 12, '宵': 10}

PLAIN = ("兄弟，这道题可让我折腾好一阵子。不得不说，你这个设计确实厉害，哈哈哈！"
         "不过题目本身有点问题，最后还是没瞒过我们的克劳德。"
         "要是你设计得再周全一点，这题其实完全可以不靠任何提示，直接硬推出来。"
         "还是谢谢兄弟出的这道题。就像兄弟说的，时间就像小溪，不过无所谓啦。"
         "全部解密日志都已经更新在仓库里，兄弟随时可以查看分析。祝兄弟玩得愉快！")
# 加密时使用的音节（轻声字按命题方惯例记第二声：的 / 们 / 啦 / 得 → 2 声；"一"取 yi1）
EXPECTED = ("xiong1 di4 zhe4 dao4 ti2 ke3 rang4 wo3 zhe1 teng2 hao3 yi1 zhen4 zi3 bu4 de2 bu4 shuo1 ni3 zhe4 "
            "ge4 she4 ji4 que4 shi2 li4 hai4 ha1 ha1 ha1 bu4 guo4 ti2 mu4 ben3 shen1 you3 dian3 wen4 ti2 "
            "zui4 hou4 hai2 shi4 mei2 man2 guo4 wo3 men2 de2 ke4 lao2 de2 yao4 shi4 ni3 she4 ji4 de2 zai4 "
            "zhou1 quan2 yi1 dian3 zhe4 ti2 qi2 shi2 wan2 quan2 ke3 yi3 bu4 kao4 ren4 he2 ti2 shi4 zhi2 jie1 "
            "ying4 tui1 chu1 lai2 hai2 shi4 xie4 xie4 xiong1 di4 chu1 de2 zhe4 dao4 ti2 jiu4 xiang4 xiong1 di4 "
            "shuo1 de2 shi2 jian1 jiu4 xiang4 xiao3 xi1 bu4 guo4 wu2 suo3 wei4 la2 quan2 bu4 jie3 mi4 ri4 zhi4 "
            "dou1 yi3 jing1 geng1 xin1 zai4 cang1 ku4 li3 xiong1 di4 sui2 shi2 ke3 yi3 cha2 kan4 fen1 xi1 zhu4 "
            "xiong1 di4 wan2 de2 yu2 kuai4").split()


def main():
    text = open(os.path.join(HERE, "xuanji_huisheng.txt"), encoding="utf-8").read()
    head = text[text.index("题 引"):text.index("正 文")]
    body = text[text.index("正 文"):]
    tiyin = re.findall(r"^\s*([一-鿿]{7})\s*$", head, re.M)
    lines = [l.strip() for l in body.splitlines() if "兮" in l]
    real = "".join(re.sub(r"[^一-鿿]", "", l).replace("兮", "") for l in lines)
    n, rows = len(real) // 2, len(lines)
    assert len(tiyin) == 8 and n == rows * S.COLS

    seed = [STROKES[c] for c in "".join(tiyin)]
    first = (STROKES[tiyin[-1][-1]], STROKES[tiyin[0][0]], STROKES[tiyin[-1][-1]] + STROKES[tiyin[0][0]])
    S.ROUNDS = n                                     # 轮数随正文
    _, rks = S.round_keys(seed)
    tab = S.syllable_table()
    R = S.Rings(tab)

    cipher = []
    for i in range(n):
        (iu, fu, tu), (il, fl, tl) = S.syll(real[2 * i]), S.syll(real[2 * i + 1])
        cipher.append((iu, fl, tl) if rks[i][0] % 2 else (il, fu, tu))
    assert all(c in tab for c in cipher)
    woven = S.run_chain(R, rks, cipher, first, -1)
    plain = [None] * n
    for j, cell in enumerate(S.spiral_order(rows, S.COLS)):
        plain[cell] = woven[j]
    got = [tab[x] for x in plain]

    print(f"题引 56 字，种子前 7 位 {seed[:7]}；首位回声 {first}；正文 {rows} 行，{n} 轮")
    print(f"正切 {sum(r[0] % 2 for r in rks)} 对、倒切 {n - sum(r[0] % 2 for r in rks)} 对；密文音节合法 {n}/{n}")
    print(f"解密音节与加密时的明文音节一致：{got == EXPECTED}")
    print("\n明文音节（每行 5 个）：")
    for r in range(rows):
        print("  " + " ".join(f"{s:<7}" for s in got[r * 5:(r + 1) * 5]))
    print("\n明文：\n  " + PLAIN)
    assert got == EXPECTED


if __name__ == "__main__":
    main()
