import os
import sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from data import TEXT, PY, TIYIN, ZHENGWEN_LINES
from strokes import STROKES
from legal import I23, F23, LEGAL_TONELESS, LEGAL_TONED, split23
from pypinyin.contrib.tone_convert import to_initials, to_finals

# toned syllables of text, S23 split
SYL = [(PY[c][3], PY[c][2]) for c in TEXT]

# ---------- alphabets: each = (Ilist, Flist, decomp(s)->(i,f), legal set of (i,f), toned legal of (i,f,t)) ----------
def mk_s23(Ilist, Flist):
    leg = {split23(s) for s in LEGAL_TONELESS}
    legt = {split23(s) + (t,) for s, t in LEGAL_TONED}
    return Ilist, Flist, split23, leg, legt

def strict(s):
    i = to_initials(s + '1', strict=True); f = to_finals(s + '1', strict=True)
    if i in ('zh','ch','sh','r','z','c','s') and f == 'i': f = '-i'
    return i, f

alph = {}
# A
alph['A'] = mk_s23(I23, F23)
alph['A-'] = mk_s23(I23, [f for f in F23 if f not in ('', 'g', 'ng')])
# B
IB = ['b','p','m','f','d','t','n','l','g','k','h','j','q','x','zh','ch','sh','r','z','c','s','y','w','']
FB24 = ['a','o','e','i','u','v','ai','ei','ui','ao','ou','iu','ie','ve','er','an','en','in','un','vn','ang','eng','ing','ong']
FB = FB24 + sorted(f for f in F23 if f not in FB24 and f not in ('', 'g', 'ng'))
alph['B'] = mk_s23(IB, FB)
# C strict
IC = ['b','p','m','f','d','t','n','l','g','k','h','j','q','x','zh','ch','sh','r','z','c','s','']
FC35 = ['a','o','e','-i','er','ai','ei','ao','ou','an','en','ang','eng','ong','i','ia','ie','iao','iou','ian','in','iang','ing','iong',
        'u','ua','uo','uai','uei','uan','uen','uang','ueng','v','ve','van','vn']
legC = {strict(s) for s in LEGAL_TONELESS}
legCt = {strict(s) + (t,) for s, t in LEGAL_TONED}
extraC = sorted({f for i, f in legC} - set(FC35))
alph['C'] = (IC, FC35, strict, legC, legCt)
# D first occurrence in TEXT (S23)
ID, FD = [], []
for s, t in SYL:
    i, f = split23(s)
    if i not in ID: ID.append(i)
    if f not in FD: FD.append(f)
alph['D'] = mk_s23(ID, FD)

def encode(name, syl, tmod):
    Il, Fl, dec, leg, legt = alph[name]
    out = []
    for s, t in syl:
        i, f = dec(s)
        if i not in Il or f not in Fl: return None
        tt = t - 1
        out.append((Il.index(i), Fl.index(f), tt % tmod))
    return np.array(out)

def legal_mats(name, tmod):
    Il, Fl, dec, leg, legt = alph[name]
    L = np.zeros((len(Il), len(Fl)), bool)
    LT = np.zeros((len(Il), len(Fl), tmod), bool)
    for a, i in enumerate(Il):
        for b, f in enumerate(Fl):
            L[a, b] = (i, f) in leg
            for t in range(tmod):
                LT[a, b, t] = (i, f, t + 1) in legt
    return L, LT

def seqs(arr):
    out = {'text': arr, 'rev': arr[::-1].copy()}
    # 23 rows x 10 cols, column-major
    g = arr.reshape(23, 10, 3)
    out['col23x10'] = g.transpose(1, 0, 2).reshape(230, 3).copy()
    return out

def chain(arr, mods):
    d = arr.copy()
    d[1:] = (arr[1:] - arr[:-1]) % mods
    return d

def analyze(arr, mods, L, LT, pmax=60):
    nI, nF, nT = mods
    # per position shift-validity matrix: V[j,sI,sF] = L[(a-sI)%nI,(b-sF)%nF]
    ai = (arr[:, 0:1] - np.arange(nI)[None, :]) % nI  # (n,nI)
    bf = (arr[:, 1:2] - np.arange(nF)[None, :]) % nF
    V = L[ai[:, :, None], bf[:, None, :]]  # (n,nI,nF)
    tt = (arr[:, 2:3] - np.arange(nT)[None, :]) % nT
    VT = LT[ai[:, :, None, None], bf[:, None, :, None], tt[:, None, None, :]]  # (n,nI,nF,nT)
    res = {}
    for p in range(1, pmax + 1):
        full = 0; full_nz = 0; keys = []
        for r in range(p):
            idx = np.arange(r, len(arr), p)
            m = VT[idx].all(axis=0)
            cnt = int(m.sum())
            nz = cnt - int(m[0, 0, 0])
            if cnt: full += 1
            if nz: full_nz += 1
            keys.append(np.argwhere(m))
        res[p] = (full, full_nz, keys)
    return res

if __name__ == '__main__':
    random.seed(1)
    NCTRL = 20
    summary = []
    for name in ['A', 'A-', 'B', 'C', 'D']:
        for tmod in (4, 5):
            base = encode(name, SYL, tmod)
            if base is None:
                print(name, tmod, 'encode failed'); continue
            Il, Fl = alph[name][0], alph[name][1]
            mods = np.array([len(Il), len(Fl), tmod])
            L, LT = legal_mats(name, tmod)
            S = seqs(base)
            S['chain'] = chain(base, mods)
            S['chain_rev'] = chain(base[::-1].copy(), mods)
            for sname, arr in S.items():
                r = analyze(arr, mods, L, LT)
                best = max(range(1, 61), key=lambda p: (r[p][0] / p, -p))
                best_nz = max(range(1, 61), key=lambda p: (r[p][1] / p, -p))
                allfull = [p for p in range(1, 61) if r[p][0] == p]
                allnz = [p for p in range(1, 61) if r[p][1] == p]
                # controls
                cfull = []; cnz = []; cmin_full = []; cmin_nz = []
                for k in range(NCTRL):
                    perm = list(range(230)); random.shuffle(perm)
                    sh = base[perm]
                    carr = chain(sh, mods) if sname.startswith('chain') else sh
                    rc = analyze(carr, mods, L, LT)
                    cfull.append(max(rc[p][0] / p for p in range(1, 61)))
                    cnz.append(max(rc[p][1] / p for p in range(1, 61)))
                    cmin_full.append(min([p for p in range(1, 61) if rc[p][0] == p] or [99]))
                    cmin_nz.append(min([p for p in range(1, 61) if rc[p][1] == p] or [99]))
                line = (f"{name:3s} T{tmod} {sname:9s} | any-shift: max={r[best][0]}/{best} allfull_p_min={min(allfull) if allfull else '-'} "
                        f"#allfull_p={len(allfull)} | nonzero-shift: max={r[best_nz][1]}/{best_nz} allnz_p_min={min(allnz) if allnz else '-'} "
                        f"| ctrl any max={np.mean(cfull):.3f} minP_allfull={np.median(cmin_full)} ; ctrl nz max={np.mean(cnz):.3f} minP_allnz={np.median(cmin_nz)}")
                print(line, flush=True)
                # frac curve small p
                curve = ' '.join(f"{p}:{r[p][0]}/{r[p][1]}" for p in (1,2,3,4,5,6,7,8,10,14,23,46,56,60))
                print('      p:full/nz ', curve, flush=True)
                summary.append((name, tmod, sname, r))
    import pickle
    pickle.dump([(a, b, c, {p: (v[0], v[1]) for p, v in r.items()}) for a, b, c, r in summary], open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'summary.pkl'), 'wb'))
