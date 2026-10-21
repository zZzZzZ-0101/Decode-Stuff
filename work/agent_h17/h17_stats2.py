import sys, math, random
sys.path.insert(0, '/home/user/Decode-Stuff/work')
sys.path.insert(0, '/home/user/Decode-Stuff/work/agent_h17')
from collections import Counter, defaultdict
import numpy as np
from data import TEXT, CLAUSES, FREQ, PY, TIYIN
from strokes import STROKES
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    from h17_stats import chi2_sf

rng = np.random.default_rng(777)
N = len(TEXT)
ini = [PY[c][0] for c in TEXT]; fin = [PY[c][1] for c in TEXT]; ton = [PY[c][2] for c in TEXT]
pz = ['P' if t in (1, 2) else 'Z' for t in ton]
NS = 5000

def perm_p(stat_fn, seq, obs, nsim=NS, greater=True):
    seq = list(seq); cnt = 0
    for _ in range(nsim):
        s = list(rng.permutation(seq))
        v = stat_fn(s)
        cnt += (v >= obs) if greater else (v <= obs)
    return (cnt + 1) / (nsim + 1)

print("\n=== 3. 平仄 / 句末 / 押韵 ===")
pat = Counter(''.join(pz[i * 5:(i + 1) * 5]) for i in range(46))
print("平 count", pz.count('P'), "仄", pz.count('Z'))
print("clause 平仄 patterns (top):", pat.most_common(10), "distinct=", len(pat))
# chi2 vs binomial-independent expectation using marginal p
pP = pz.count('P') / N
exp = {}
import itertools
for t in itertools.product('PZ', repeat=5):
    k = ''.join(t); exp[k] = 46 * np.prod([pP if x == 'P' else 1 - pP for x in k])
def pat_stat(s):
    c = Counter(''.join(s[i * 5:(i + 1) * 5]) for i in range(46))
    return sum((c.get(k, 0) - e) ** 2 / e for k, e in exp.items())
x0 = pat_stat(pz); print(f"pattern chi2 vs indep={x0:.1f}; perm p={perm_p(pat_stat, pz, x0, 5000):.3g}")
# slot-wise tone distribution
slot_t = [Counter(ton[i] for i in range(N) if i % 5 == s) for s in range(5)]
print("tone by slot:", [dict(sorted(c.items())) for c in slot_t])
def slot_chi(s):
    tab = np.zeros((5, 4))
    for i, t in enumerate(s): tab[i % 5, t - 1] += 1
    e = tab.sum(1, keepdims=True) * tab.sum(0, keepdims=True) / tab.sum()
    return ((tab - e) ** 2 / e).sum()
x0 = slot_chi(ton); print(f"slot x tone chi2={x0:.2f} df=12 asym p={chi2_sf(x0,12):.3g}; perm p={perm_p(slot_chi, ton, x0, 5000):.3g}")
end_t = Counter(ton[i * 5 + 4] for i in range(46)); print("clause-final tone:", dict(sorted(end_t.items())))
# 2nd/4th char 平仄 alternation (律句 rule: pos2 != pos4)
def alt24(s): return sum(1 for i in range(46) if (s[i*5+1] in (1,2)) != (s[i*5+3] in (1,2)))
a0 = alt24(ton); print(f"pos2/pos4 平仄相反 clauses={a0}/46; perm p(>=)={perm_p(alt24, ton, a0, 5000):.3g}")
# line-internal: clause A end vs clause B end 平仄 opposite (对句)
def opp_end(s): return sum(1 for L in range(23) if (s[L*10+4] in (1,2)) != (s[L*10+9] in (1,2)))
o0 = opp_end(ton); print(f"line 上下分句末字平仄相反={o0}/23; perm p(>=)={perm_p(opp_end, ton, o0, 5000):.3g}")
# rhyme: adjacent clause-final same final / same 十三辙
ZHE = {'a':'fa','ia':'fa','ua':'fa','o':'bo','uo':'bo','e':'ge','ie':'ye','ue':'ye','ve':'ye','i':'yq','v':'yq','er':'yq',
       'ai':'hl','uai':'hl','ei':'hd','ui':'hd','ao':'yt','iao':'yt','ou':'yq2','iu':'yq2','an':'yq3','ian':'yq3','uan':'yq3',
       'en':'rc','in':'rc','un':'rc','ang':'jy','iang':'jy','uang':'jy','eng':'zd','ing':'zd','ong':'zd','iong':'zd','u':'gs'}
def zhe(i):
    f = fin[i]; s = PY[TEXT[i]][3]
    if f == 'u' and s[0] in 'jqxy': return 'yq'  # ü
    if f == 'i' and s in ('zhi','chi','shi','ri','zi','ci','si'): return 'yq'
    return ZHE.get(f, f)
ends = [i * 5 + 4 for i in range(46)]
def rhyme_counts(fseq):
    adj = sum(1 for k in range(45) if fseq[ends[k]] == fseq[ends[k + 1]])
    inline = sum(1 for L in range(23) if fseq[ends[2*L]] == fseq[ends[2*L+1]])
    even = sum(1 for k in range(0, 22) if fseq[ends[2*k+1]] == fseq[ends[2*k+3]])  # 偶句末相邻
    return adj, inline, even
zseq = [zhe(i) for i in range(N)]
for label, seq in [("韵母", fin), ("十三辙", zseq)]:
    obs = rhyme_counts(seq)
    endvals = [seq[e] for e in ends]
    sims = []
    for _ in range(NS):
        p = list(rng.permutation(endvals)); full = list(seq)
        for k, e in enumerate(ends): full[e] = p[k]
        sims.append(rhyme_counts(full))
    sims = np.array(sims)
    ps = [(sims[:, j] >= obs[j]).mean() for j in range(3)]
    print(f"{label}: adj-clause same={obs[0]}/45 (E={sims[:,0].mean():.2f}, p={ps[0]:.3g}); within-line={obs[1]}/23 (E={sims[:,1].mean():.2f}, p={ps[1]:.3g}); even-clause chain={obs[2]}/22 (E={sims[:,2].mean():.2f}, p={ps[2]:.3g})")
print("even-clause endings:", ''.join(CLAUSES[2*L+1][-1] for L in range(23)), [fin[ends[2*L+1]] for L in range(23)])

print("\n=== 4. 周期性 IC / 自相关 / Kasiski ===")
def ic(seq):
    c = Counter(seq); n = len(seq)
    return sum(v * (v - 1) for v in c.values()) / (n * (n - 1)) if n > 1 else 0
def ic_period(seq, p): return np.mean([ic(seq[k::p]) for k in range(p)])
def coinc(seq, d): return sum(1 for i in range(len(seq) - d) if seq[i] == seq[i + d]) / (len(seq) - d)
for label, seq in [("声母", ini), ("韵母", fin), ("声调", ton), ("字", list(TEXT))]:
    base = ic(seq)
    obs_ic = np.array([ic_period(seq, p) for p in range(1, 61)])
    obs_co = np.array([coinc(seq, d) for d in range(1, 61)])
    sims_ic = np.zeros((300, 60)); sims_co = np.zeros((300, 60))
    for s in range(300):
        q = list(rng.permutation(seq))
        sims_ic[s] = [ic_period(q, p) for p in range(1, 61)]
        sims_co[s] = [coinc(q, d) for d in range(1, 61)]
    zic = (obs_ic - sims_ic.mean(0)) / sims_ic.std(0).clip(1e-9)
    zco = (obs_co - sims_co.mean(0)) / sims_co.std(0).clip(1e-9)
    top_ic = sorted(range(60), key=lambda k: -zic[k])[:4]
    top_co = sorted(range(60), key=lambda k: -zco[k])[:4]
    low_co = sorted(range(60), key=lambda k: zco[k])[:3]
    # global max-z test: compare max z across lags to shuffled max z
    maxz_null = []
    for s in range(300):
        maxz_null.append(((sims_co[s] - sims_co.mean(0)) / sims_co.std(0).clip(1e-9)).max())
    p_max = (np.array(maxz_null) >= zco.max()).mean()
    print(f"{label}: IC={base:.4f} (uniform-alphabet 1/k={1/len(set(seq)):.4f}); "
          f"period IC top z: {[(k+1, round(zic[k],2)) for k in top_ic]}; "
          f"lag-coinc top z: {[(k+1, round(zco[k],2)) for k in top_co]}; low z: {[(k+1, round(zco[k],2)) for k in low_co]}; "
          f"max-z over lags={zco.max():.2f} p_global={p_max:.3f}; lag1 coinc obs={obs_co[0]:.4f} vs shuf {sims_co[:,0].mean():.4f}")
# Kasiski: repeated char bigrams/trigrams and toned-syllable bigrams
syl = [(PY[c][3], PY[c][2]) for c in TEXT]
for label, seq in [("字", list(TEXT)), ("带调音节", syl), ("声调", ton)]:
    for n in ((2, 3) if label != "声调" else (4, 5, 6)):
        pos = defaultdict(list)
        for i in range(N - n + 1): pos[tuple(seq[i:i + n])].append(i)
        reps = {k: v for k, v in pos.items() if len(v) > 1}
        dists = [b - a for v in reps.values() for a, b in zip(v, v[1:])]
        nrep = sum(len(v) - 1 for v in reps.values())
        sim = []
        for _ in range(500):
            idx = rng.permutation(len(seq)); q = [seq[j] for j in idx]; pp = Counter(tuple(q[i:i + n]) for i in range(N - n + 1))
            sim.append(sum(v - 1 for v in pp.values() if v > 1))
        sim = np.array(sim)
        g = 0
        for d in dists: g = math.gcd(g, d)
        dm5 = Counter(d % 5 for d in dists)
        print(f"Kasiski {label} {n}-gram: repeats={nrep} (shuffle mean {sim.mean():.2f}, P(>=)={(sim>=nrep).mean():.3f}); dists={sorted(dists)[:15]} gcd={g} d%5={dict(dm5)}"
              + (f" e.g. {[(''.join(k) if label=='字' else k, v) for k,v in list(reps.items())[:6]]}" if label != '声调' else ''))
