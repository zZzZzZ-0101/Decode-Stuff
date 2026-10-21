"""织位候选：返回 index 列表 idx，使明文 text[k] = woven[idx[k]]。"""
N = 115


def grids(w):
    h = -(-N // w)
    return h, w


def perms():
    P = {}
    P["恒等"] = list(range(N))
    P["倒序"] = list(range(N))[::-1]
    # 两端交错：woven = t0 t114 t1 t113 ...
    inter = []
    for k in range(N):
        inter.append(k // 2 if k % 2 == 0 else N - 1 - k // 2)
    P["交错织入"] = [inter.index(j) for j in range(N)]       # woven[j] = text[inter[j]]
    P["交错读出"] = inter                                     # text[k] = woven[inter[k]]
    # 对折：前半正读 + 后半倒读
    h = (N + 1) // 2
    fold = list(range(h)) + list(range(N - 1, h - 1, -1))
    P["对折读出"] = fold
    P["对折织入"] = [fold.index(j) for j in range(N)]
    # 奇偶分轨：偶位正向、奇位反向
    eo = [None] * N
    ev = list(range(0, N, 2)); od = list(range(1, N, 2))[::-1]
    order = ev + od
    P["奇偶回文读出"] = order
    P["奇偶回文织入"] = [order.index(j) for j in range(N)]
    for w in (5, 23):
        hgt = N // w
        # 蛇形（牛耕）
        snake = []
        for r in range(hgt):
            row = list(range(r * w, r * w + w))
            snake += row if r % 2 == 0 else row[::-1]
        P[f"蛇形行宽{w}"] = snake
        # 按列读
        col = [r * w + c for c in range(w) for r in range(hgt)]
        P[f"列读宽{w}"] = col
        P[f"列写宽{w}"] = [col.index(j) for j in range(N)]
        # 列蛇形
        cs = []
        for c in range(w):
            colc = [r * w + c for r in range(hgt)]
            cs += colc if c % 2 == 0 else colc[::-1]
        P[f"列蛇读宽{w}"] = cs
        P[f"列蛇写宽{w}"] = [cs.index(j) for j in range(N)]
        # 螺旋
        top, bot, lef, rig = 0, hgt - 1, 0, w - 1
        sp = []
        while top <= bot and lef <= rig:
            sp += [top * w + c for c in range(lef, rig + 1)]; top += 1
            sp += [r * w + rig for r in range(top, bot + 1)]; rig -= 1
            if top <= bot:
                sp += [bot * w + c for c in range(rig, lef - 1, -1)]; bot -= 1
            if lef <= rig:
                sp += [r * w + lef for r in range(bot, top - 1, -1)]; lef += 1
        P[f"螺旋读宽{w}"] = sp
        P[f"螺旋写宽{w}"] = [sp.index(j) for j in range(N)]
    for k in list(P):
        P[k + "·倒"] = P[k][::-1]
    return P


def rail_order(n, rails):
    """栅栏（之字形）书写后按行读出的位置序列"""
    pat = list(range(rails)) + list(range(rails - 2, 0, -1))
    rows = [pat[i % len(pat)] for i in range(n)]
    return sorted(range(n), key=lambda i: (rows[i], i))


def more_perms():
    P = {}
    for b in range(2, 24):
        idx = []
        for s in range(0, N, b):
            idx += list(range(s, min(s + b, N)))[::-1]
        P[f"块内倒序{b}"] = idx
        blocks = [list(range(s, min(s + b, N))) for s in range(0, N, b)]
        P[f"块序倒排{b}"] = [j for blk in blocks[::-1] for j in blk]
        P[f"隔块回文{b}"] = [j for k, blk in enumerate(blocks) for j in (blk if k % 2 == 0 else blk[::-1])]
    for k in range(2, 8):
        tracks = [list(range(t, N, k)) for t in range(k)]
        order = [j for tr in tracks for j in tr]          # 按轨抽取
        P[f"{k}轨读出"] = order
        P[f"{k}轨织入"] = [order.index(j) for j in range(N)]
    for r in range(2, 13):
        ro = rail_order(N, r)
        P[f"栅栏{r}·读"] = ro                              # text 写成之字形后按行读 → woven
        P[f"栅栏{r}·写"] = [ro.index(j) for j in range(N)]
    for k in list(P):
        P[k + "·倒"] = P[k][::-1]
    return P


def grid_perms():
    P = {}
    for w in range(2, 24):
        hgt = -(-N // w)
        pos = {(r, c): r * w + c for r in range(hgt) for c in range(w) if r * w + c < N}
        col = [pos[(r, c)] for c in range(w) for r in range(hgt) if (r, c) in pos]
        csn = []
        for c in range(w):
            colc = [pos[(r, c)] for r in range(hgt) if (r, c) in pos]
            csn += colc if c % 2 == 0 else colc[::-1]
        rsn = []
        for r in range(hgt):
            row = [pos[(r, c)] for c in range(w) if (r, c) in pos]
            rsn += row if r % 2 == 0 else row[::-1]
        for name, o in ((f"列读{w}", col), (f"列蛇{w}", csn), (f"行蛇{w}", rsn)):
            P[name + "·读"] = o
            P[name + "·写"] = [o.index(j) for j in range(N)]
    for k in list(P):
        P[k + "·倒"] = P[k][::-1]
    return P


def spiral_cells(h, w, corner, cw):
    """从指定角出发、顺/逆时针的"回"字形遍历，返回 (r,c) 序列"""
    grid_r = list(range(h)); grid_c = list(range(w))
    top, bot, lef, rig = 0, h - 1, 0, w - 1
    out = []
    # 统一在标准方向上生成，再做镜像变换
    while top <= bot and lef <= rig:
        out += [(top, c) for c in range(lef, rig + 1)]; top += 1
        out += [(r, rig) for r in range(top, bot + 1)]; rig -= 1
        if top <= bot:
            out += [(bot, c) for c in range(rig, lef - 1, -1)]; bot -= 1
        if lef <= rig:
            out += [(r, lef) for r in range(bot, top - 1, -1)]; lef += 1
    if not cw:   # 逆时针 = 沿主对角线转置后的顺时针（仅方阵严格成立；非方阵改用行列镜像）
        out = [(r, w - 1 - c) for r, c in out]
        out = out  # 镜像后方向反转
    tr = {0: lambda r, c: (r, c), 1: lambda r, c: (r, w - 1 - c),
          2: lambda r, c: (h - 1 - r, c), 3: lambda r, c: (h - 1 - r, w - 1 - c)}[corner]
    return [tr(r, c) for r, c in out]


def spiral_perms():
    P = {}
    for h, w in ((23, 5), (5, 23)):
        for corner in range(4):
            for cw in (True, False):
                cells = spiral_cells(h, w, corner, cw)
                order = [r * w + c for r, c in cells]
                assert sorted(order) == list(range(N))
                tag = f"回字{h}x{w}角{corner}{'顺' if cw else '逆'}"
                P[tag + "·读"] = order
                P[tag + "·写"] = [order.index(j) for j in range(N)]
    for k in list(P):
        P[k + "·倒"] = P[k][::-1]
    return P


def diag_perms():
    """斜线扫描与各宽度的"回"字形同心环"""
    P = {}
    for w in range(2, 24):
        h = -(-N // w)
        cells = {(r, c) for r in range(h) for c in range(w) if r * w + c < N}
        # 反对角线（r+c 恒定），方向交替 = 之字形（JPEG 式）
        for zig in (False, True):
            order = []
            for s in range(h + w - 1):
                diag = [(r, s - r) for r in range(h) if (r, s - r) in cells]
                if zig and s % 2: diag = diag[::-1]
                order += [r * w + c for r, c in diag]
            P[f"斜扫{w}{'之字' if zig else ''}"] = order
        # 主对角线（c-r 恒定）
        order = []
        for d in range(-(h - 1), w):
            order += [r * w + (r + d) for r in range(h) if (r, r + d) in cells]
        P[f"主斜{w}"] = order
        # 各宽度的"回"字形（螺旋），仅对完整网格的格子取序
        top, bot, lef, rig = 0, h - 1, 0, w - 1
        sp = []
        while top <= bot and lef <= rig:
            sp += [(top, c) for c in range(lef, rig + 1)]; top += 1
            sp += [(r, rig) for r in range(top, bot + 1)]; rig -= 1
            if top <= bot:
                sp += [(bot, c) for c in range(rig, lef - 1, -1)]; bot -= 1
            if lef <= rig:
                sp += [(r, lef) for r in range(bot, top - 1, -1)]; lef += 1
        P[f"回字{w}"] = [r * w + c for r, c in sp if (r, c) in cells]
    out = {}
    for k, o in P.items():
        if sorted(o) != list(range(N)): continue
        for name, idx in ((k + "·读", o), (k + "·写", [o.index(j) for j in range(N)])):
            out[name] = idx
            out[name + "·倒"] = idx[::-1]
    return out
