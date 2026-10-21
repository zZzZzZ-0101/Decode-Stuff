import os
import sys, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from data import TEXT, PY, STROKES
from legal import LEGAL_TONED, LEGAL_TONELESS
rng = np.random.default_rng(7)
def chi2(M):
    M = np.asarray(M, float); E = M.sum(1, keepdims=True) * M.sum(0, keepdims=True) / M.sum()
    return ((M - E)**2 / np.where(E>0, E, 1)).sum()
def table(x, y):
    xs = sorted(set(x)); ys = sorted(set(y)); M = np.zeros((len(xs), len(ys)), int)
    for a, b in zip(x, y): M[xs.index(a), ys.index(b)] += 1
    return xs, ys, M
def permp(x, y, n=5000):
    _, _, M = table(x, y); c0 = chi2(M); y = np.array(y); cnt = 0
    for _ in range(n):
        cnt += chi2(table(x, list(rng.permutation(y)))[2]) >= c0
    return c0, (cnt+1)/(n+1), M
def icls(i):
    if i in ('b','d','g','j','zh','z'): return '1unasp'
    if i in ('p','t','k','q','ch','c'): return '2asp'
    if i in ('f','h','x','sh','s'): return '3vlfric'
    return '4voiced'
for scope, chars in [('tokens230', list(TEXT)), ('unique', sorted(set(TEXT)))]:
    tone = [PY[c][2] for c in chars]
    for name, y in [('stroke_parity', [STROKES[c]%2 for c in chars]),
                    ('init_class4', [icls(PY[c][0]) for c in chars]),
                    ('init_class3', [icls(PY[c][0]).replace('3vlfric','1unasp') for c in chars])]:
        c0, p, M = permp(tone, y, 3000)
        print('H12', scope, 'tone(rows %s) x %s'%(sorted(set(tone)), name), M.tolist(), 'chi2=%.2f perm_p=%.3f'%(c0, p))
# (b) phase-0 pair effect: position-preserving baseline (shuffle within the same 10-col row position)
INI = {c: PY[c][0] for c in TEXT}
def legal_pairs(text):
    r = []
    for k in range(0, 230, 2):
        a, b = text[k], text[k+1]
        r.append(((PY[a][0]+PY[b][1], PY[b][2]) in LEGAL_TONED, (PY[b][0]+PY[a][1], PY[a][2]) in LEGAL_TONED))
    return np.array(r)
real = legal_pairs(TEXT)
print('(b) phase0 IF %.3f FI %.3f'%tuple(real.mean(0)))
pos = np.arange(230) % 10
by = [np.flatnonzero(pos==j) for j in range(10)]
B = []
for _ in range(1000):
    t = list(TEXT)
    for ix in by:
        perm = rng.permutation(ix)
        for a, b in zip(ix, perm): t[a] = TEXT[b]
    B.append(legal_pairs(t).mean(0))
B = np.array(B)
print('(b) phase0 column-preserving baseline: IF mean %.3f max %.3f p=%.3f | FI mean %.3f max %.3f p=%.3f'%(
    B[:,0].mean(), B[:,0].max(), (B[:,0]>=real[:,0].mean()).mean(), B[:,1].mean(), B[:,1].max(), (B[:,1]>=real[:,1].mean()).mean()))
# breakdown by row-pair position
for j in range(5):
    print('  pair cols (%d,%d) IF %.3f FI %.3f'%(2*j, 2*j+1, real[j::5,0].mean(), real[j::5,1].mean()))
# how many pairs are same-initial-type / rhyming? share final?
same_fin = np.mean([PY[TEXT[k]][1]==PY[TEXT[k+1]][1] for k in range(0,230,2)])
print('share final in phase0 pairs %.3f'%same_fin)
