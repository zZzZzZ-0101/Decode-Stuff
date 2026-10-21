import sys, math, random
sys.path.insert(0, '/home/user/Decode-Stuff/work')
from data import *
from legal import *
import numpy as np
from pypinyin import pinyin, Style

N = 230
# ---------- S21 legal sets ----------
def s21(ch, het=False):
    ini = pinyin(ch, style=Style.INITIALS, strict=True, heteronym=het)[0]
    fin = pinyin(ch, style=Style.FINALS_TONE3, strict=True, heteronym=het, neutral_tone_with_five=True)[0]
    return ini, fin
LEG21 = set(); LEG21T = set()
for ch in GB:
    inis, fins = s21(ch, True)
    # heteronym lists may misalign; recompute per reading via TONE3 full
    for p in pinyin(ch, style=Style.TONE3, heteronym=True, neutral_tone_with_five=True)[0]:
        pass
for ch in GB:
    ps = pinyin(ch, style=Style.TONE3, heteronym=True, neutral_tone_with_five=True)[0]
    for p in ps:
        if not p[-1].isdigit(): continue
        t = int(p[-1]); s = p[:-1]
        from pypinyin.style._utils import get_initials, get_finals
        i = get_initials(s, strict=True); f = get_finals(s, strict=True)
        LEG21.add((i, f)); LEG21T.add((i, f, t))
from pypinyin.style._utils import get_initials, get_finals
P21 = {}
for c in set(TEXT):
    ini, fin, tone, s = PY[c]
    P21[c] = (get_initials(s, strict=True), get_finals(s, strict=True), tone)

# ---------- orders (lists of TEXT indices) ----------
def idx(line, half, k): return line*10 + half*5 + k   # 0-based
orders = {}
orders['a_text'] = list(range(N))
orders['b_rev'] = list(range(N))[::-1]
orders['c_col'] = [r*10+c for c in range(10) for r in range(23)]
orders['d_boustro'] = [r*10+(c if r%2==0 else 9-c) for r in range(23) for c in range(10)]
vis = []
for k in range(12):
    vis += [k*10+c for c in range(10)]
    if k+12 < 23: vis += [(k+12)*10+c for c in range(10)]
orders['e_visual'] = vis
orders['f_interleave_in_line'] = [r*10+h*5+k for r in range(23) for k in range(5) for h in range(2)]
vi = []
for k in range(12):
    if k+12 < 23:
        for c in range(10): vi += [k*10+c, (k+12)*10+c]
    else:
        vi += [k*10+c for c in range(10)]
orders['f2_interleave_visual_cols'] = vi
for o in orders.values(): assert sorted(o) == list(range(N))

def streams(order, scheme):
    chars = [TEXT[i] for i in order]
    if scheme == 'S23':
        I = [PY[c][0] for c in chars]; F = [PY[c][1] for c in chars]; T = [PY[c][2] for c in chars]
    else:
        I = [P21[c][0] for c in chars]; F = [P21[c][1] for c in chars]; T = [P21[c][2] for c in chars]
    return I, F, T

def build_mats(I, F, scheme):
    iu = sorted(set(I)); fu = sorted(set(F))
    ii = np.array([iu.index(x) for x in I]); fi = np.array([fu.index(x) for x in F])
    L = np.zeros((len(iu), len(fu)), bool); LT = np.zeros((len(iu), len(fu), 6), bool)
    for a, x in enumerate(iu):
        for b, y in enumerate(fu):
            if scheme == 'S23':
                L[a, b] = is_legal(x, y)
                for t in range(1, 6): LT[a, b, t] = is_legal(x, y, t)
            else:
                L[a, b] = (x, y) in LEG21
                for t in range(1, 6): LT[a, b, t] = (x, y, t) in LEG21T
    return ii, fi, L, LT

rng = np.random.default_rng(0)
out = []
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); out.append(s)

# baseline
for scheme in ['S23', 'S21']:
    I, F, T = streams(orders['a_text'], scheme)
    ii, fi, L, LT = build_mats(I, F, scheme)
    tt = np.array(T)
    r = []; rt = []
    for _ in range(1000):
        p = rng.permutation(N)
        r.append(L[ii, fi[p]].mean()); rt.append(LT[ii, fi[p], tt[p]].mean())
    P(f'BASELINE {scheme}: toneless mean={np.mean(r):.4f} max={np.max(r):.4f} | toned(tone w/ fin) mean={np.mean(rt):.4f} max={np.max(rt):.4f}')

ar = np.arange(N)
YUE = [idx(11,1,0), idx(21,1,0)]; CHUAN = idx(5,0,2)
assert TEXT[YUE[0]] == '月' and TEXT[YUE[1]] == '月' and TEXT[CHUAN] == '川'
results = {}
for oname, order in orders.items():
    pos = {t: k for k, t in enumerate(order)}
    for scheme in ['S23', 'S21']:
        I, F, T = streams(order, scheme)
        ii, fi, L, LT = build_mats(I, F, scheme)
        tt = np.array(T)
        # shift
        sh = np.array([L[ii, fi[(ar+d) % N]].mean() for d in range(N)])
        order_d = np.argsort(-sh)
        nz = [d for d in order_d if d != 0]
        bestd = nz[0]
        # toned: fin shift d, tone shift e (independent), all d,e
        best_te = (0, None, None)
        for d in range(N):
            fsh = fi[(ar+d) % N]
            for e in range(N):
                if d == 0 and e == 0: continue
                v = LT[ii, fsh, tt[(ar+e) % N]].mean()
                if v > best_te[0]: best_te = (v, d, e)
        # H16 d
        h16 = []
        for y in YUE:
            d = (pos[CHUAN] - pos[y]) % N
            for dd in (d, (-d) % N):
                h16.append((dd, round(sh[dd], 4)))
        # affine full
        bestA = (0, None, None); bestAT = (0, None, None)
        for a in range(1, N):
            if math.gcd(a, N) != 1: continue
            perm = (a*ar[None, :] + ar[:, None]) % N   # rows b
            v = L[ii[None, :], fi[perm]].mean(1)
            vt = LT[ii[None, :], fi[perm], tt[perm]].mean(1)
            if a == 1: v[0] = -1; vt[0] = -1
            b = int(np.argmax(v)); bt = int(np.argmax(vt))
            if v[b] > bestA[0]: bestA = (v[b], a, b)
            if vt[bt] > bestAT[0]: bestAT = (vt[bt], a, bt)
        # block affine (clauses of 5, rows of 10) in this order's stream
        blk = {}
        for bs in (5, 10):
            M = N // bs; best = (0, None, None)
            for a in range(1, M):
                if math.gcd(a, M) != 1: continue
                for b in range(M):
                    if a == 1 and b == 0: continue
                    perm = np.array([((a*(i//bs)+b) % M)*bs + i % bs for i in range(N)])
                    v = L[ii, fi[perm]].mean()
                    if v > best[0]: best = (v, a, b)
            blk[bs] = best
        P(f'[{oname} {scheme}] shift best d={bestd} rate={sh[bestd]:.4f} (top3: {[(int(d), round(sh[d],4)) for d in nz[:3]]}); '
          f'toned best (d,e)=({best_te[1]},{best_te[2]}) rate={best_te[0]:.4f}; '
          f'affine best a={bestA[1]} b={bestA[2]} rate={bestA[0]:.4f}; affine toned a={bestAT[1]} b={bestAT[2]} {bestAT[0]:.4f}; '
          f'clause-affine {tuple(round(x,4) if isinstance(x,float) else x for x in blk[5])}; row-affine {tuple(round(x,4) if isinstance(x,float) else x for x in blk[10])}; H16 d->rate {h16}')
        results[(oname, scheme)] = (bestd, sh[bestd], I, F, T, order)

# failure examples for overall best shift
best = max(results.items(), key=lambda kv: kv[1][1])
(oname, scheme), (d, r, I, F, T, order) = best
fails = [(k, TEXT[order[k]], I[k], F[(k+d) % N], I[k]+F[(k+d) % N]) for k in range(N) if not (is_legal(I[k], F[(k+d) % N]) if scheme=='S23' else (I[k], F[(k+d) % N]) in LEG21)]
P(f'OVERALL best shift: {oname} {scheme} d={d} rate={r:.4f}; fails={len(fails)}; examples: {fails[:6]}')
open('/home/user/Decode-Stuff/work/agent_h1/results.txt', 'w').write('\n'.join(out))
