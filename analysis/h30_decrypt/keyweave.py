"""密钥驱动的织位候选：约瑟夫环、按轮钥排序、步进回填。返回 idx，使 text[k] = woven[idx[k]]。"""
N = 115


def josephus(steps):
    """steps: 可迭代的步长；每次从当前位置数过 step 个剩余格取出"""
    alive = list(range(N)); out = []; pos = 0
    for s in steps:
        if not alive: break
        pos = (pos + s - 1) % len(alive)
        out.append(alive.pop(pos))
    return out


def probe_fill(steps):
    """位置累加步长，若已占用则顺延到下一个空位"""
    used = [False] * N; pos = 0; out = []
    for s in steps:
        pos = (pos + s) % N
        while used[pos]: pos = (pos + 1) % N
        used[pos] = True; out.append(pos)
    return out


def candidates(rk, extra_streams=None):
    P = {}
    for m in range(1, N + 1):
        P[f"约瑟夫步长{m}"] = josephus([m] * N)
    streams = {f"rk{j}": [r[j] for r in rk] for j in range(3)}
    streams["rk和"] = [sum(r) for r in rk]
    streams["rk0+rk1"] = [r[0] + r[1] for r in rk]
    if extra_streams: streams.update(extra_streams)
    for name, st in streams.items():
        P[f"约瑟夫·{name}"] = josephus(st)
        P[f"回填·{name}"] = probe_fill(st)
        P[f"排序·{name}"] = sorted(range(N), key=lambda i: (st[i], i))
        P[f"排序倒·{name}"] = sorted(range(N), key=lambda i: (-st[i], i))
    out = {}
    for k, o in P.items():
        if sorted(o) != list(range(N)): continue
        out[k + "·读"] = o                                   # text[k] = woven[o[k]]
        out[k + "·写"] = [o.index(j) for j in range(N)]       # woven[k] = text[o[k]]
    return out
