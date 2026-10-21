# 56 态《四处补遗》自同步验证与 115 音节完整对照脚本
import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(ROOT, "analysis"))
if os.path.isdir("/tmp/pylib/pypinyin"):
    sys.path.insert(0, "/tmp/pylib")
else:
    for d in os.listdir("/tmp/pylib") if os.path.isdir("/tmp/pylib") else []:
        sys.path.insert(0, os.path.join("/tmp/pylib", d))

from decode import (
    RAW_SEED,
    INI_ORDER,
    FIN_ORDER,
    LEGAL_SYLLS,
    CHAR_MAP,
    ini_ring,
    fin_ring,
    tone_ring,
    decrypt_56,
)

def step_one(i, prev_pt, ct_sylls, rk_list):
    ic, fc, tc = ct_sylls[i]
    k0, k1, k2 = rk_list[i]
    pi, pf, pt = prev_pt
    k_I = k0 + FIN_ORDER.index(pf)
    k_F = k1 + pt
    k_T = k2 + INI_ORDER.index(pi)
    curr_i, curr_f, curr_t = ic, fc, tc
    if i % 3 == 0:
        steps = ["I", "F", "T"]
    elif i % 3 == 1:
        steps = ["F", "T", "I"]
    else:
        steps = ["T", "I", "F"]
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
    return (curr_i, curr_f, curr_t)

if __name__ == "__main__":
    sbox, rk_list, ct_sylls, pts = decrypt_56()
    all_s = sorted(LEGAL_SYLLS)[:200]
    hit37 = 0
    hit46 = 0
    for s0 in all_s:
        cur = s0
        for i in range(31, 52):
            cur = step_one(i, cur, ct_sylls, rk_list)
            if i == 37 and cur == pts[37]:
                hit37 += 1
            if i == 46 and cur == pts[46]:
                hit46 += 1
    print(f"=== 语境子环链式自同步验证 ===")
    print(f"从 i=30 任取 200 个初始音节状态推进：")
    print(f"  在 i=37 ('却是十一六' 起点) 自动收敛至真解的比例: {hit37}/200")
    print(f"  在 i=46 ('千秋二〇二三' 起点) 自动收敛至真解的比例: {hit46}/200\n")
    print("=== 115 个位置解密音节与候选汉字 ===")
    for i, s in enumerate(pts):
        cands = "".join(CHAR_MAP.get(s, [])[:6])
        print(f"{i:3d}: {s[0]+s[1]+str(s[2]):8s} | {cands}")
