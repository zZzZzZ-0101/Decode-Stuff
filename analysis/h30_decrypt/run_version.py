"""用当前环境中的 pypinyin 版本跑完整解密并打分（供多版本对比）。"""
import sys, os, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pypinyin
from spec import round_keys, make_sbox, Rings, decrypt, REAL
from lm import load_lexicon, segment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from legal import GB
from pypinyin import pinyin, Style


def split_t3(t, strict=True):
    from pypinyin.style._utils import get_initials, get_finals
    base = t[:-1]
    i = get_initials(base, strict=strict)
    f = get_finals(base, strict=strict)
    return i, f


def main():
    lex = load_lexicon()
    tab = {}
    for ch in GB:
        t = pinyin(ch, style=Style.TONE3)[0][0]
        if t[-1] in "1234":
            i = pinyin(ch, style=Style.INITIALS, strict=True)[0][0]
            f = pinyin(ch, style=Style.FINALS, strict=True)[0][0]
            if f: tab[(i, f, int(t[-1]))] = t
    INI = sorted({a for a, _, _ in tab}); FIN = sorted({b for _, b, _ in tab})
    R = Rings(INI, FIN, set(tab))
    rk = round_keys(make_sbox(True, True, "A"))
    cs = []
    for k in range(115):
        u, l = REAL[2 * k], REAL[2 * k + 1]
        def sy(c):
            t = pinyin(c, style=Style.TONE3)[0][0]
            return (pinyin(c, style=Style.INITIALS, strict=True)[0][0],
                    pinyin(c, style=Style.FINALS, strict=True)[0][0], int(t[-1]) if t[-1].isdigit() else 5)
        iu, fu, tu = sy(u); il, fl, tl = sy(l)
        cs.append((iu, fl, tl) if rk[k][0] % 2 else (il, fu, tu))
    bad = [k for k, c in enumerate(cs) if c not in tab]
    if bad:
        print(pypinyin.__version__, len(tab), "密文非法", bad); return
    p = [tab[x] for x in decrypt(cs, rk, R)]
    cov, segs = segment(p, lex)
    print(pypinyin.__version__, len(tab), "覆盖", cov, " ".join(p[:40]))


if __name__ == "__main__":
    main()
