import sys, math
sys.path.insert(0, '/home/user/Decode-Stuff/work')
from collections import Counter
import numpy as np
from data import TEXT, CLAUSES, FREQ, PY, TIYIN
from strokes import STROKES
rng = np.random.default_rng(99)
N = len(TEXT); NS = 20000
cls = np.array([FREQ[c] for c in TEXT])
print("=== 5. H19 ===")
tab = np.zeros((4, 5), int)
for i, k in enumerate(cls): tab[k - 1, i % 5] += 1
print("class x slot table (rows class1..4, cols slot1..5):\n", tab)
def chi(cl):
    t = np.zeros((4, 5))
    np.add.at(t, (cl - 1, np.arange(N) % 5), 1)
    e = t.sum(1, keepdims=True) * t.sum(0, keepdims=True) / t.sum()
    return ((t - e) ** 2 / e).sum()
# permutation must permute characters (tokens), so class multiset preserved
chars = np.array(list(TEXT))
def perm_cls():
    q = rng.permutation(chars); f = Counter(q); return np.array([f[c] for c in q])
x0 = chi(cls); sims = np.array([chi(cls[rng.permutation(N)]) for _ in range(NS)])
print(f"class x slot chi2={x0:.2f} df=12, perm p={(sims>=x0).mean():.3g}")
hap_slot = Counter(i % 5 + 1 for i in range(N) if cls[i] == 1)
print("hapax slot dist:", dict(sorted(hap_slot.items())), "(E=17.2 each)")
def hchi(cl):
    c = np.bincount(np.arange(N)[cl == 1] % 5, minlength=5); e = (cl == 1).sum() / 5
    return ((c - e) ** 2 / e).sum()
h0 = hchi(cls); hs = np.array([hchi(cls[rng.permutation(N)]) for _ in range(NS)])
print(f"hapax slot chi2={h0:.2f} df=4, perm p={(hs>=h0).mean():.3g}")
# per-clause hapax count & class sum vs 题引 strokes
ti = ''.join(TIYIN); ts = np.array([STROKES[c] for c in ti])
hc = np.array([(cls[k*5:(k+1)*5] == 1).sum() for k in range(46)])
cs = np.array([cls[k*5:(k+1)*5].sum() for k in range(46)])
def rank(a): return np.argsort(np.argsort(a + rng.random(len(a)) * 1e-9))
def spear(a, b): return np.corrcoef(rank(a), rank(b))[0, 1]
for name, v in [("hapax/clause", hc), ("classsum/clause", cs)]:
    for off in (0, 10):
        s = ts[off:off + 46]
        r0 = spear(v, s); rs = np.array([spear(v[rng.permutation(46)], s) for _ in range(5000)])
        print(f"{name} vs 题引 strokes[{off}:{off+46}] spearman={r0:.3f}, two-sided perm p={(np.abs(rs)>=abs(r0)).mean():.3g}")
# per-position: class seq vs strokes of the char itself (sanity) and vs 题引 strokes cycled
st = np.array([STROKES[c] for c in TEXT])
r0 = spear(cls, st); rs = np.array([spear(cls, st[rng.permutation(N)]) for _ in range(3000)])
print(f"class vs own-char strokes spearman={r0:.3f}, p={(np.abs(rs)>=abs(r0)).mean():.3g}")
# hapax count per clause distribution vs shuffle
print("hapax per clause dist:", dict(sorted(Counter(hc).items())))
# within-clause repeated chars & within-line repeats
def rep_in(cl_len):
    return lambda seq: sum(1 for k in range(N // cl_len) if len(set(seq[k*cl_len:(k+1)*cl_len])) < cl_len)
for L, lab in [(5, "clause"), (10, "line")]:
    f = rep_in(L); o = f(list(TEXT)); s = np.array([f(list(rng.permutation(chars))) for _ in range(NS)])
    print(f"{lab}s with a repeated char: obs={o}, shuffle E={s.mean():.2f}, P(<=obs)={(s<=o).mean():.3g}")
# min distance between repeats of same char
pos = {}
md = []
for i, c in enumerate(TEXT):
    if c in pos: md.append(i - pos[c])
    pos[c] = i
print("min gap between same-char repeats:", min(md), "gaps<5:", sum(1 for d in md if d < 5), "gaps<10:", sum(1 for d in md if d < 10))
def gaps(seq):
    p = {}; g = []
    for i, c in enumerate(seq):
        if c in p: g.append(i - p[c])
        p[c] = i
    return min(g), sum(1 for d in g if d < 10)
sg = np.array([gaps(list(rng.permutation(chars))) for _ in range(5000)])
print(f"shuffle: min-gap mean={sg[:,0].mean():.2f}, P(min>={min(md)})={(sg[:,0]>=min(md)).mean():.3g}; gaps<10 E={sg[:,1].mean():.2f}, P(<=obs)={(sg[:,1]<=sum(1 for d in md if d<10)).mean():.3g}")

# freq-of-freq profile 86/37/10/10, max=4: how unusual under natural (Zipf) sampling vs uniform
prof = sorted(Counter(FREQ.values()).items()); print("profile", prof)
def sample_profile(p, n=N):
    c = np.bincount(rng.choice(len(p), n, p=p)); c = c[c > 0]
    return len(c), c.max(), (c == 4).sum(), (c == 3).sum()
for model in ["uniform", "zipf1.0", "zipf0.7"]:
    # tune vocab V so E[types]≈143
    best = None
    for V in range(150, 4000, 10):
        if model == "uniform": p = np.ones(V) / V
        else:
            a = float(model[4:]); p = 1 / np.arange(1, V + 1) ** a; p /= p.sum()
        et = np.mean([sample_profile(p)[0] for _ in range(60)])
        if best is None or abs(et - 143) < abs(best[1] - 143): best = (V, et, p)
        if et > 150: break
    V, et, p = best
    res = np.array([sample_profile(p) for _ in range(20000)])
    ok_types = np.abs(res[:, 0] - 143) <= 5
    print(f"{model}: V={V} E[types]={res[:,0].mean():.1f}; max-count dist={dict(sorted(Counter(res[:,1]).items()))}; "
          f"P(max<=4)={(res[:,1]<=4).mean():.3g}; P(max==4 & n4==10 & n3==10 | types~143)={((res[:,1]==4)&(res[:,2]==10)&(res[:,3]==10)&ok_types).sum()/ok_types.sum():.3g}; "
          f"P(n4>=10 & max<=4)={((res[:,1]<=4)&(res[:,2]>=10)).mean():.3g}")
