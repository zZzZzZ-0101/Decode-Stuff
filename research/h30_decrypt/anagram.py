"""诊断：对一组音节做不受约束的重排搜索（模拟退火），看能达到多高的连读覆盖。
真明文的音节组应能重排到接近真实文本的水平；混有错误音节的组则明显达不到。"""
import math, random


def anneal(sylls, cov, iters=12000, seed=0, T0=3.0):
    rnd = random.Random(seed)
    cur = sylls[:]; rnd.shuffle(cur)
    sc = cov(cur); best, bsc = cur[:], sc
    n = len(cur)
    for t in range(iters):
        T = T0 * (1 - t / iters) + 0.05
        nxt = cur[:]
        if rnd.random() < 0.5:
            a, b = rnd.randrange(n), rnd.randrange(n); nxt[a], nxt[b] = nxt[b], nxt[a]
        else:   # 搬移一段
            a = rnd.randrange(n); L = rnd.randint(1, 4); seg = nxt[a:a + L]; del nxt[a:a + L]
            c = rnd.randrange(len(nxt) + 1); nxt[c:c] = seg
        s = cov(nxt)
        if s >= sc or rnd.random() < math.exp((s - sc) / T):
            cur, sc = nxt, s
            if sc > bsc: best, bsc = cur[:], sc
    return bsc, best
