"""带密钥列序的列移位反演：woven 切成 w 段（每段 h），各段可倒置，按列序拼成 h 行读出。"""
import itertools, math


def rows_from(blocks, order, flips):
    cols = [blocks[k][::-1] if f else blocks[k] for k, f in zip(order, flips)]
    h = len(cols[0])
    return [cols[c][r] for r in range(h) for c in range(len(cols))]


def brute5(p, score):
    blocks = [p[i * 23:(i + 1) * 23] for i in range(5)]
    best = []
    for order in itertools.permutations(range(5)):
        for flips in itertools.product((0, 1), repeat=5):
            best.append((score(rows_from(blocks, order, flips)), order, flips))
    best.sort(reverse=True)
    return best[:5]


def beam23(p, pair_score, width=400):
    """23 列（每列 5）：按相邻列同一行的双音词得分做集束搜索"""
    blocks = [p[i * 5:(i + 1) * 5] for i in range(23)]
    nodes = [(k, f) for k in range(23) for f in (0, 1)]
    col = {(k, f): (blocks[k][::-1] if f else blocks[k]) for k, f in nodes}
    S = {(a, b): sum(pair_score(col[a][r], col[b][r]) for r in range(5)) for a in nodes for b in nodes if a[0] != b[0]}
    beam = [((n,), 0.0) for n in nodes]
    for _ in range(22):
        nxt = []
        for path, sc in beam:
            used = {k for k, _ in path}
            for n in nodes:
                if n[0] not in used:
                    nxt.append((path + (n,), sc + S[(path[-1], n)]))
        nxt.sort(key=lambda x: -x[1]); beam = nxt[:width]
    return [(sc, [col[n] for n in path]) for path, sc in beam[:3]]
