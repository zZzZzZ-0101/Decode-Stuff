"""通用网格织位：沿 write 路径依次写入明文（只占前 N 格），再沿 read 路径读出（跳过空格）。"""
N = 115


def paths(h, w):
    P = {}
    P["行"] = [(r, c) for r in range(h) for c in range(w)]
    P["列"] = [(r, c) for c in range(w) for r in range(h)]
    P["行蛇"] = [(r, c) for r in range(h) for c in (range(w) if r % 2 == 0 else range(w - 1, -1, -1))]
    P["列蛇"] = [(r, c) for c in range(w) for r in (range(h) if c % 2 == 0 else range(h - 1, -1, -1))]
    top, bot, lef, rig = 0, h - 1, 0, w - 1
    sp = []
    while top <= bot and lef <= rig:
        sp += [(top, c) for c in range(lef, rig + 1)]; top += 1
        sp += [(r, rig) for r in range(top, bot + 1)]; rig -= 1
        if top <= bot:
            sp += [(bot, c) for c in range(rig, lef - 1, -1)]; bot -= 1
        if lef <= rig:
            sp += [(r, lef) for r in range(bot, top - 1, -1)]; lef += 1
    for k, tr in enumerate((lambda r, c: (r, c), lambda r, c: (r, w - 1 - c),
                            lambda r, c: (h - 1 - r, c), lambda r, c: (h - 1 - r, w - 1 - c))):
        s = [tr(r, c) for r, c in sp]
        P[f"螺旋{k}"] = s
        P[f"螺旋{k}外扩"] = s[::-1]
    dz = []
    for d in range(h + w - 1):
        cells = [(r, d - r) for r in range(h) if 0 <= d - r < w]
        dz += cells if d % 2 == 0 else cells[::-1]
    P["斜之字"] = dz
    return P


def weaves():
    out = {}
    shapes = [(h, w) for h in range(2, 61) for w in range(2, 61) if N <= h * w <= 130]
    for h, w in shapes:
        P = paths(h, w)
        for wn, wp in P.items():
            filled = set(wp[:N])
            pos = {cell: k for k, cell in enumerate(wp[:N])}     # 格 → 明文序号
            for rn, rp in P.items():
                if rn == wn: continue
                woven_from = [pos[cell] for cell in rp if cell in filled]   # woven[j] = text[woven_from[j]]
                inv = [0] * N
                for j, k in enumerate(woven_from): inv[k] = j
                out[f"{h}x{w} 写{wn}读{rn}"] = inv                 # text[k] = woven[inv[k]]
    return out
