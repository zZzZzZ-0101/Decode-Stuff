"""带调拼音词库与可读性打分（词频取自 jieba dict.txt，路径由环境变量 JIEBA_DICT 指定）。"""
import os, re, math, pickle
from pypinyin import pinyin, Style, lazy_pinyin

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lex.pkl")


def build_lexicon(path, minfreq=20):
    lex = {}
    for line in open(path, encoding="utf8"):
        w, f = line.split()[:2]
        f = int(f)
        if f < minfreq or not re.fullmatch(r"[一-鿿]{2,4}", w):
            continue
        key = tuple(lazy_pinyin(w, style=Style.TONE3, neutral_tone_with_five=True))
        lex[key] = max(lex.get(key, 0), f)
    return lex


def load_lexicon():
    if os.path.exists(CACHE):
        return pickle.load(open(CACHE, "rb"))
    lex = build_lexicon(os.environ.get("JIEBA_DICT"))
    pickle.dump(lex, open(CACHE, "wb"))
    return lex


def segment(sylls, lex, neutral_ok=True):
    """最大化词频对数之和的切分；返回 (被多字词覆盖的音节数, 切分结果)"""
    n = len(sylls)
    best = [(-1e18, 0, None)] * (n + 1)
    best[0] = (0.0, 0, None)
    for i in range(n):
        sc, cov, _ = best[i]
        if sc < -1e17: continue
        if sc - 3.0 > best[i + 1][0]:
            best[i + 1] = (sc - 3.0, cov, (i, 1))
        for L in (2, 3, 4):
            if i + L > n: break
            key = tuple(sylls[i:i + L])
            f = lex.get(key)
            if f is None and neutral_ok:
                key2 = key[:-1] + (key[-1][:-1] + "5",)
                f = lex.get(key2)
            if f:
                s = sc + math.log(f) + 2.0 * L
                if s > best[i + L][0]:
                    best[i + L] = (s, cov + L, (i, L))
    segs, j = [], n
    while j > 0:
        i, L = best[j][2]
        segs.append(" ".join(sylls[i:i + L]) if L > 1 else sylls[i])
        j = i
    return best[n][1], segs[::-1]
