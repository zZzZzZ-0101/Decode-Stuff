import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from legal import GB
from data import split_py, TEXT, PY
def icls(i):
    if i in ('b','d','g','j','zh','z'): return 0
    if i in ('p','t','k','q','ch','c'): return 1
    if i in ('f','h','x','sh','s'): return 2
    return 3
L = np.zeros((4,4))
for ch in GB[:3755]:
    i, f, t, s = split_py(ch)[0]
    if 1 <= t <= 4: L[t-1, icls(i)] += 1
O = np.zeros((4,4))
for c in TEXT:
    i, f, t, s = PY[c]; O[t-1, icls(i)] += 1
E = L / L.sum() * O.sum()
chi = ((O-E)**2/E).sum()
rng = np.random.default_rng(1); P = (L/L.sum()).ravel(); sims = []
for _ in range(5000):
    S = rng.multinomial(int(O.sum()), P).reshape(4,4); sims.append(((S-E)**2/E).sum())
print('lexicon(GB 3755) row%:', np.round(L/L.sum(0,keepdims=True)*100).astype(int).tolist())
print('text tone x class GOF vs lexicon: chi2=%.2f MC p=%.3f'%(chi, (np.array(sims)>=chi).mean()))
