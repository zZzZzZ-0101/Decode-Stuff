# 《四处补遗》56 长状态机、S-Box 四约定消融与 115 对反切及子环解密验证脚本
import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(ROOT, "analysis"))
if os.path.isdir("/tmp/pylib/pypinyin"):
    sys.path.insert(0, "/tmp/pylib")
else:
    for d in os.listdir("/tmp/pylib") if os.path.isdir("/tmp/pylib") else []:
        sys.path.insert(0, os.path.join("/tmp/pylib", d))

from collections import Counter
from data import TIYIN, TEXT, STROKES
from decode import (
    RAW_SEED, LEGAL_SYLLS, CHAR_MAP, INI_ORDER, FIN_ORDER,
    char_syll, decrypt_56
)

def verify_sbox_conventions():
    cnt = Counter(RAW_SEED)
    conventions = {
        "(-cnt, +v) [次数降序, 值升序]": lambda v: (-cnt[v], v),
        "(-cnt, -v) [次数降序, 值降序]": lambda v: (-cnt[v], -v),
        "(+cnt, +v) [次数升序, 值升序]": lambda v: (cnt[v], v),
        "(+cnt, -v) [次数升序, 值降序]": lambda v: (cnt[v], -v),
    }
    print("=== 1. S-Box 四种排序约定消融实验 ===")
    for name, key_fn in conventions.items():
        order = sorted(range(1, 18), key=key_fn)
        sbox = [order.index(v + 1) for v in range(17)]
        S = [(v - 1) % 17 for v in RAW_SEED]
        legal_count = 0
        for i in range(115):
            a = [sbox[(S[j] + i) % 17] for j in range(56)]
            b = [(a[j] + a[(j + 1) % 56] + a[(j + 7) % 56]) % 17 for j in range(56)]
            r = (b[0] + b[7] + b[8]) % 56
            S = b[r:] + b[:r]
            rk0 = S[i % 56] + 1
            u, l = TEXT[2 * i], TEXT[2 * i + 1]
            iu, fu, tu = char_syll(u)
            il, fl, tl = char_syll(l)
            syll = (iu, fl, tl) if rk0 % 2 == 1 else (il, fu, tu)
            if syll in LEGAL_SYLLS:
                legal_count += 1
        print(f"  {name}: 合法反切音节 = {legal_count} / 115")
    print()

if __name__ == "__main__":
    verify_sbox_conventions()
    sbox, rk_list, ct_sylls, pts = decrypt_56()
    print("=== 2. 56 长状态机子环解密结果 (115 音节) ===")
    for r in range(23):
        cells = []
        for c in range(5):
            idx = r * 5 + c
            s = pts[idx]
            py = s[0] + s[1] + str(s[2])
            ch = "".join(CHAR_MAP.get(s, [])[:3])
            cells.append(f"{idx:3d}:{py:7s}({ch})")
        print(f"Row {r:2d}: " + " | ".join(cells))
