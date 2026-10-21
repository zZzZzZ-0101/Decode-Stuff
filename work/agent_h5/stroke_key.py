import sys, random
sys.path.insert(0, '/home/user/Decode-Stuff/work'); sys.path.insert(0, '/home/user/Decode-Stuff/work/agent_h5')
import numpy as np
from h56 import alph, encode, legal_mats, seqs, chain, SYL
from data import TIYIN
from strokes import STROKES
random.seed(2)
KS = [STROKES[c] for c in ''.join(TIYIN)]           # 56
KL = [sum(STROKES[c] for c in l) for l in TIYIN]      # 8 per-line sums
keys = {'k56': KS, 'k7(line1)': KS[:7], 'k8linesum': KL}
def frac(arr, mods, LT, k, sign):
    K = np.array([k[i % len(k)] for i in range(len(arr))])
    a = (arr[:,0] - sign*K) % mods[0]; b = (arr[:,1] - sign*K) % mods[1]; t = (arr[:,2] - sign*K) % mods[2]
    return LT[a, b, t].mean()
for name in ['A','B','C','D']:
    for tmod in (4,5):
        base = encode(name, SYL, tmod); mods = np.array([len(alph[name][0]), len(alph[name][1]), tmod])
        L, LT = legal_mats(name, tmod)
        S = seqs(base); S['chain'] = chain(base, mods)
        for sn, arr in S.items():
            out = []
            for kn, k in keys.items():
                for sg in (1,-1):
                    f = frac(arr, mods, LT, k, sg)
                    rnd = [frac(arr, mods, LT, random.sample(k, len(k)) if len(k)>1 else k, sg) for _ in range(20)]
                    out.append(f"{kn}{'-' if sg==1 else '+'}={f:.2f}(r{np.mean(rnd):.2f}/{max(rnd):.2f})")
            print(f"{name} T{tmod} {sn:9s}", ' '.join(out), flush=True)
