import os
import sys, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collections import Counter, defaultdict
import numpy as np
from data import TEXT, CLAUSES, FREQ, PY, TIYIN
from legal import LEGAL_TONED, LEGAL_TONELESS, I23, F23, GB, split23
from strokes import STROKES
from pypinyin import pinyin, Style

rng = np.random.default_rng(12345)
random.seed(12345)

# ---------- chi2 survival via regularized incomplete gamma ----------
def gammq(a, x):
    if x <= 0: return 1.0
    if x < a + 1:
        ap, s, d = a, 1.0 / a, 1.0 / a
        for _ in range(10000):
            ap += 1; d *= x / ap; s += d
            if abs(d) < abs(s) * 1e-15: break
        return 1 - s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    b = x + 1 - a; c = 1e300; d = 1 / b; h = d
    for i in range(1, 10000):
        an = -i * (i - a); b += 2
        d = an * d + b; d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c; c = 1e-300 if abs(c) < 1e-300 else c
        d = 1 / d; de = d * c; h *= de
        if abs(de - 1) < 1e-15: break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h

def chi2_sf(x, df): return gammq(df / 2, x / 2)

def chisq(obs_counter, probs, pool_min=5, n=None):
    """probs: dict cat->p (sum 1). pool cells with expected<pool_min into one cell."""
    n = n or sum(obs_counter.values())
    cats = set(probs) | set(obs_counter)
    big, small_o, small_e = [], 0, 0.0
    zero_exp_obs = 0
    for k in cats:
        e = probs.get(k, 0) * n; o = obs_counter.get(k, 0)
        if e == 0:
            zero_exp_obs += o; continue
        if e < pool_min: small_o += o; small_e += e
        else: big.append((o, e))
    if small_e > 0: big.append((small_o, small_e))
    x = sum((o - e) ** 2 / e for o, e in big)
    df = len(big) - 1
    return x, df, chi2_sf(x, df), zero_exp_obs

def mc_chisq(obs_counter, probs, nsim=20000):
    """Monte-Carlo p for the unpooled chi2 (robust to small expectations)."""
    cats = sorted(probs); p = np.array([probs[k] for k in cats]); n = sum(obs_counter.values())
    e = p * n
    o = np.array([obs_counter.get(k, 0) for k in cats])
    x0 = ((o - e) ** 2 / e).sum()
    sims = rng.multinomial(n, p, size=nsim)
    xs = ((sims - e) ** 2 / e).sum(axis=1)
    return x0, (1 + (xs >= x0).sum()) / (nsim + 1)

def toned_split(s, t):
    i, f = split23(s); return i, f, t

ini_obs = Counter(PY[c][0] for c in TEXT)
fin_obs = Counter(PY[c][1] for c in TEXT)
ton_obs = Counter(PY[c][2] for c in TEXT)
syl_obs = Counter((PY[c][3], PY[c][2]) for c in TEXT)
N = len(TEXT)
print("=== 1. marginal chi-square ===")
print("tones obs", dict(sorted(ton_obs.items())))

def norm(d):
    s = sum(d.values()); return {k: v / s for k, v in d.items()}

# (a) machine alphabet uniform
P_a_ini = {i: 1 / len(I23) for i in I23}
P_a_fin = {f: 1 / len(F23) for f in F23}
P_a_ton4 = {t: 0.25 for t in (1, 2, 3, 4)}
P_a_ton5 = {t: 0.2 for t in (1, 2, 3, 4, 5)}
# (b) uniform over legal toned syllables
lt = list(LEGAL_TONED)
P_b_ini = norm(Counter(split23(s)[0] for s, t in lt))
P_b_fin = norm(Counter(split23(s)[1] for s, t in lt))
P_b_ton = norm(Counter(t for s, t in lt))
# (c) common text approx: each GB char's primary reading, equal weight; also GB level-1 (3755)
def char_dist(chars):
    I, F, T = Counter(), Counter(), Counter()
    for ch in chars:
        p = pinyin(ch, style=Style.TONE3, neutral_tone_with_five=True)[0][0]
        t = int(p[-1]) if p[-1].isdigit() else 5
        s = p.rstrip('012345'); i, f = split23(s)
        I[i] += 1; F[f] += 1; T[t] += 1
    return norm(I), norm(F), norm(T)
P_c_ini, P_c_fin, P_c_ton = char_dist(GB)
P_c1_ini, P_c1_fin, P_c1_ton = char_dist(GB[:3755])

rows = []
for name, obs, models in [
    ("声母", ini_obs, [("a 机器均匀(24含零)", P_a_ini), ("b 合法带调音节均匀", P_b_ini), ("c GB6763等权", P_c_ini), ("c' GB一级3755等权", P_c1_ini)]),
    ("韵母", fin_obs, [("a 机器均匀(37)", P_a_fin), ("b 合法带调音节均匀", P_b_fin), ("c GB6763等权", P_c_fin), ("c' GB一级3755等权", P_c1_fin)]),
    ("声调", ton_obs, [("a 机器均匀(4调)", P_a_ton4), ("a 机器均匀(5调)", P_a_ton5), ("b 合法带调音节均匀", P_b_ton), ("c GB6763等权", P_c_ton), ("c' GB一级3755等权", P_c1_ton)]),
]:
    for mname, P in models:
        x, df, p, z = chisq(obs, P)
        xm, pm = mc_chisq(obs, P)
        print(f"{name} | {mname}: chi2(pooled)={x:.1f} df={df} p={p:.3g} | MC unpooled chi2={xm:.1f} p_MC={pm:.3g} | obs-in-zero-exp={z}")
print("b tone probs", {k: round(v, 3) for k, v in sorted(P_b_ton.items())})
print("c tone probs", {k: round(v, 3) for k, v in sorted(P_c_ton.items())})
# top deviations finals vs c
print("finals obs vs exp(c):", [(f, fin_obs.get(f, 0), round(P_c_fin.get(f, 0) * N, 1)) for f in sorted(P_c_fin, key=lambda k: -abs(fin_obs.get(k, 0) - P_c_fin[k] * N))[:8]])
print("initials obs vs exp(c):", [(f, ini_obs.get(f, 0), round(P_c_ini.get(f, 0) * N, 1)) for f in sorted(P_c_ini, key=lambda k: -abs(ini_obs.get(k, 0) - P_c_ini[k] * N))[:8]])
# entropy
def H(c):
    n = sum(c.values()); return -sum(v / n * math.log2(v / n) for v in c.values())
print(f"entropy bits: ini {H(ini_obs):.3f} (max {math.log2(len(I23)):.3f}); fin {H(fin_obs):.3f} (max {math.log2(len(F23)):.3f}); tone {H(ton_obs):.3f} (max 2)")
print("legal toned syllables in text:", sum(1 for c in TEXT if (PY[c][3], PY[c][2]) in LEGAL_TONED), "/", N)

print("\n=== 2. distinct counts ===")
def distinct_stats(Nsym, n, obs, nsim=200000):
    E = Nsym * (1 - (1 - 1 / Nsym) ** n)
    V = Nsym * (Nsym - 1) * (1 - 2 / Nsym) ** n + Nsym * (1 - 1 / Nsym) ** n - Nsym ** 2 * (1 - 1 / Nsym) ** (2 * n)
    sims = np.array([len(np.unique(rng.integers(0, Nsym, n))) for _ in range(nsim)])
    lo, hi = np.quantile(sims, [0.0005, 0.9995])
    p_low = (sims <= obs).mean()
    z = (obs - E) / math.sqrt(V)
    return E, math.sqrt(V), lo, hi, sims.min(), p_low, z
for label, Nsym, obs in [("带调音节 (1349)", len(LEGAL_TONED), len(syl_obs)),
                         ("无调音节 (413)", len(LEGAL_TONELESS), len({PY[c][3] for c in TEXT})),
                         ("汉字 GB6763", len(GB), len(FREQ)),
                         ("汉字 GB一级3755", 3755, len(FREQ))]:
    E, sd, lo, hi, mn, pl, z = distinct_stats(Nsym, N, obs, nsim=50000)
    print(f"{label}: obs={obs}, E={E:.2f}, sd={sd:.2f}, 99.9%=[{lo:.0f},{hi:.0f}], sim min={mn}, z={z:.1f}, P(<=obs)={pl:.2g}")
print("distinct toneless syll:", len({PY[c][3] for c in TEXT}))
# syllable freq-of-freq
print("toned-syllable freq profile:", sorted(Counter(syl_obs.values()).items()))
print("max syllable repeat:", syl_obs.most_common(5))
# expected max count for uniform 1349, n=230
mx = np.array([np.bincount(rng.integers(0, 1349, N)).max() for _ in range(20000)])
print("uniform-1349 max repeat dist:", sorted(Counter(mx).items()), " obs max:", max(syl_obs.values()))
