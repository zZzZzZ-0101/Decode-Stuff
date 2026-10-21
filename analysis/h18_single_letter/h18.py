import os
import sys, itertools, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from data import TEXT, CLAUSES, ZHENGWEN_LINES, PY, STROKES
from legal import LEGAL_TONED, LEGAL_TONELESS
rng = np.random.default_rng(12345)
N = len(TEXT)
INI = sorted({PY[c][0] for c in TEXT} | {''})
FIN = sorted({PY[c][1] for c in TEXT})
ii = {x:k for k,x in enumerate(INI)}; fi = {x:k for k,x in enumerate(FIN)}
TAB = np.zeros((len(INI), len(FIN), 6), bool)   # toned legality
TABN = np.zeros((len(INI), len(FIN)), bool)     # toneless
for a in INI:
    for b in FIN:
        TABN[ii[a], fi[b]] = (a+b) in LEGAL_TONELESS
        for t in range(1,6):
            TAB[ii[a], fi[b], t] = (a+b, t) in LEGAL_TONED
Iarr = np.array([ii[PY[c][0]] for c in TEXT]); Farr = np.array([fi[PY[c][1]] for c in TEXT]); Tarr = np.array([PY[c][2] for c in TEXT])
Z = ii['']
def shuffles(n):
    for _ in range(n):
        p = rng.permutation(N); yield Iarr[p], Farr[p], Tarr[p]
NSH = 1000
out = []
def rep(*a):
    s = ' '.join(str(x) for x in a); print(s); out.append(s)

# ---------- (a) I,F,T cyclic ----------
def fam_a(I, F, T):
    res = {}
    for order in itertools.permutations('IFT'):
        for ph in range(3):
            n = (N-ph)//3
            idx = ph + 3*np.arange(n)
            pos = {r: idx+k for k, r in enumerate(order)}
            a, b, t = I[pos['I']], F[pos['F']], T[pos['T']]
            res[(''.join(order), ph)] = (TAB[a,b,t].mean(), TABN[a,b].mean())
    return res
ra = fam_a(Iarr, Farr, Tarr)
rep('== (a) IFT cyclic: order,phase -> toned, toneless')
for k,v in sorted(ra.items(), key=lambda x:-x[1][0]): rep(k, '%.3f %.3f'%v)
bA = [fam_a(*s) for s in shuffles(NSH)]
for key in [('IFT',0),('IFT',1),('IFT',2)]:
    bt = np.array([b[key][0] for b in bA]); bn = np.array([b[key][1] for b in bA])
    rep('baseline', key, 'toned mean %.3f max %.3f | toneless mean %.3f max %.3f'%(bt.mean(),bt.max(),bn.mean(),bn.max()))
btmax = np.array([max(v[0] for v in b.values()) for b in bA]); bnmax = np.array([max(v[1] for v in b.values()) for b in bA])
rep('baseline max-over-18-variants: toned mean %.3f max %.3f; toneless mean %.3f max %.3f'%(btmax.mean(),btmax.max(),bnmax.mean(),bnmax.max()))
rep('real max toned %.3f toneless %.3f'%(max(v[0] for v in ra.values()), max(v[1] for v in ra.values())))

# ---------- (b) I,F alternating ----------
def fam_b(I, F, T):
    res = {}
    for order in ['IF','FI']:
        for ph in range(2):
            n = (N-ph)//2; idx = ph + 2*np.arange(n)
            pi = idx + order.index('I'); pf = idx + order.index('F')
            a, b = I[pi], F[pf]
            res[(order, ph)] = (TAB[a,b,T[pf]].mean(), TAB[a,b,T[pi]].mean(), TABN[a,b].mean())
    return res
rb = fam_b(Iarr, Farr, Tarr)
rep('== (b) IF alternating: order,phase -> toned(T of F-char), toned(T of I-char), toneless')
for k,v in sorted(rb.items(), key=lambda x:-x[1][0]): rep(k, '%.3f %.3f %.3f'%v)
bB = [fam_b(*s) for s in shuffles(NSH)]
for j,name in enumerate(['toned_Fchar','toned_Ichar','toneless']):
    real = max(v[j] for v in rb.values()); bm = np.array([max(v[j] for v in b.values()) for b in bB])
    rep('(b)', name, 'real max %.3f | baseline(max over 4) mean %.3f max %.3f | p=%.3f'%(real, bm.mean(), bm.max(), (bm>=real).mean()))

# ---------- slot schemes (c)/(d) ----------
def schemes(L, ks):
    """enumerate slot->{I,F,T,X} assignments; syllables paired in order; I's attached order-preservingly to syllables.
    returns list of (assignment_str, [ (pi or -1, pf, pt) ... ])"""
    res = []
    for assign in itertools.product('IFTX', repeat=L):
        nF = assign.count('F'); nT = assign.count('T'); nI = assign.count('I')
        if nF != nT or nF not in ks or nI > nF: continue
        Fp = [i for i,x in enumerate(assign) if x=='F']; Tp = [i for i,x in enumerate(assign) if x=='T']; Ip = [i for i,x in enumerate(assign) if x=='I']
        for which in itertools.combinations(range(nF), nI):
            syl = []; it = iter(Ip)
            for j in range(nF):
                syl.append((next(it) if j in which else -1, Fp[j], Tp[j]))
            res.append((''.join(assign), tuple(syl)))
    return res

def block_tables(I, F, T, L):
    nb = N // L
    Ib = I.reshape(nb, L); Fb = F.reshape(nb, L); Tb = T.reshape(nb, L)
    # leg3[b, pi, pf, pt], leg2[b, pf, pt] (zero initial), toneless too
    leg3 = TAB[Ib[:,:,None,None], Fb[:,None,:,None], Tb[:,None,None,:]]
    leg2 = TAB[Z, Fb[:,:,None], Tb[:,None,:]]
    n3 = np.broadcast_to(TABN[Ib[:,:,None], Fb[:,None,:]][:,:,:,None], leg3.shape)
    n2 = np.broadcast_to(TABN[Z, Fb][:,:,None], leg2.shape)
    return leg3, leg2, n3, n2

def compile_schemes(sch, L):
    # flatten each syllable into an index into combined table of size L^3 + L^2
    maxs = max(len(s) for _,s in sch)
    idx = np.full((len(sch), maxs), -1, np.int64)
    for k,(_,syl) in enumerate(sch):
        for j,(pi,pf,pt) in enumerate(syl):
            idx[k,j] = (pi*L*L + pf*L + pt) if pi >= 0 else (L**3 + pf*L + pt)
    nsyl = (idx >= 0).sum(1)
    return idx, nsyl

def eval_schemes(idx, nsyl, I, F, T, L):
    leg3, leg2, n3, n2 = block_tables(I, F, T, L)
    nb = leg3.shape[0]
    outs = []
    for l3, l2 in [(leg3, leg2), (n3, n2)]:
        comb = np.concatenate([l3.reshape(nb, -1), l2.reshape(nb, -1), np.zeros((nb,1),bool)], 1)  # last = pad (False)
        idc = np.where(idx >= 0, idx, comb.shape[1]-1)
        g = comb[:, idc]                       # nb x nsch x maxs
        legal_syl = g.sum(0).sum(1)           # total legal syllables per scheme
        valid = (idx >= 0)[None]
        allok = (g | ~valid).all(2).sum(0)    # blocks with all syllables legal
        rate = legal_syl / (nsyl * nb)
        outs.append((rate, allok / nb))
    return outs

for fam, L, ks, nsh in [('(c) clause-5', 5, (1,2), NSH), ('(d) row-10', 10, (2,3), 200)]:
    sch = schemes(L, ks)
    idx, nsyl = compile_schemes(sch, L)
    rep('==', fam, 'n_schemes', len(sch))
    (r_t, a_t), (r_n, a_n) = eval_schemes(idx, nsyl, Iarr, Farr, Tarr, L)
    for name, r, a in [('toned', r_t, a_t), ('toneless', r_n, a_n)]:
        k = int(np.argmax(r)); ka = int(np.argmax(a))
        rep(fam, name, 'best syllable-rate %.3f scheme %s %s | best all-legal-block rate %.3f scheme %s %s'%(r[k], sch[k][0], sch[k][1], a[ka], sch[ka][0], sch[ka][1]))
        # per k (syllable count)
        for kk in ks:
            m = nsyl == kk
            kb = np.flatnonzero(m)[np.argmax(r[m])]
            rep('   k=%d best rate %.3f (%s) ; best blockrate %.3f'%(kk, r[kb], sch[kb][0], a[m].max()))
    bmax = {'toned':[], 'toneless':[], 'toned_blk':[], 'toneless_blk':[]}
    for s in shuffles(nsh):
        (bt, bat), (bn, ban) = eval_schemes(idx, nsyl, *s, L)
        bmax['toned'].append(bt.max()); bmax['toneless'].append(bn.max()); bmax['toned_blk'].append(bat.max()); bmax['toneless_blk'].append(ban.max())
    for name, real in [('toned', r_t.max()), ('toneless', r_n.max()), ('toned_blk', a_t.max()), ('toneless_blk', a_n.max())]:
        b = np.array(bmax[name]); rep(fam, 'baseline(max over schemes, %d shuffles)'%nsh, name, 'real %.3f | mean %.3f max %.3f | p=%.3f'%(real, b.mean(), b.max(), (b>=real).mean()))

# ---------- (e) variable-length DP ----------
def dp(I, F, T, toned=True):
    n = len(I)
    cnt = [0]*(n+1); cnt[0] = 1
    INF = 10**9
    cost = [INF]*(n+1); cost[0] = 0      # min number of illegal syllables (any segmentation)
    reach = [False]*(n+1); reach[0] = True
    for p in range(n):
        if cost[p] >= INF: continue
        # 3-letter: I nonempty
        if p+3 <= n:
            ok3 = (I[p] != Z) and (TAB[I[p],F[p+1],T[p+2]] if toned else TABN[I[p],F[p+1]])
            if ok3: cnt[p+3] += cnt[p]
            cost[p+3] = min(cost[p+3], cost[p] + (0 if ok3 else 1))
        if p+2 <= n:
            ok2 = TAB[Z,F[p],T[p+1]] if toned else TABN[Z,F[p]]
            if ok2: cnt[p+2] += cnt[p]
            cost[p+2] = min(cost[p+2], cost[p] + (0 if ok2 else 1))
    # longest legal prefix
    good = [False]*(n+1); good[0] = True
    for p in range(n):
        if not good[p]: continue
        if p+3 <= n and I[p] != Z and (TAB[I[p],F[p+1],T[p+2]] if toned else TABN[I[p],F[p+1]]): good[p+3] = True
        if p+2 <= n and (TAB[Z,F[p],T[p+1]] if toned else TABN[Z,F[p]]): good[p+2] = True
    lp = max(i for i in range(n+1) if good[i])
    return cnt[n], cost[n], lp
for toned in (True, False):
    c, mc, lp = dp(list(Iarr), list(Farr), list(Tarr), toned)
    B = [dp(list(a), list(b), list(t), toned) for a,b,t in shuffles(NSH)]
    bc = np.array([x[0] for x in B], float); bm = np.array([x[1] for x in B]); bl = np.array([x[2] for x in B])
    rep('== (e) DP toned=%s: real n_seg=%d, min_illegal_syllables=%d, longest_legal_prefix=%d/230'%(toned, c, mc, lp))
    rep('   baseline: P(n_seg>0)=%.3f, n_seg mean %.2f max %d; min_illegal mean %.2f min %d; prefix mean %.1f max %d; p(min_illegal<=real)=%.3f p(prefix>=real)=%.3f'%(
        (bc>0).mean(), bc.mean(), bc.max(), bm.mean(), bm.min(), bl.mean(), bl.max(), (bm<=mc).mean(), (bl>=lp).mean()))

# ---------- H12 ----------
from scipy.stats import chi2_contingency
def icls(i):
    if i in ('b','d','g','j','zh','z'): return 'unasp'
    if i in ('p','t','k','q','ch','c'): return 'asp'
    if i in ('f','h','x','sh','s'): return 'vlfric'
    return 'voiced'   # m n l r y w ''
def ctab(pairs, rows, cols):
    M = np.zeros((len(rows), len(cols)), int)
    for r,c in pairs: M[rows.index(r), cols.index(c)] += 1
    M = M[:, M.sum(0)>0]; M = M[M.sum(1)>0]
    return M
for scope, chars in [('tokens230', list(TEXT)), ('unique', sorted(set(TEXT)))]:
    tones = sorted({PY[c][2] for c in chars})
    M = ctab([(PY[c][2], STROKES[c]%2) for c in chars], tones, [0,1])
    chi, p, dof, _ = chi2_contingency(M); rep('H12', scope, 'tone x stroke-parity', M.tolist(), 'chi2=%.2f dof=%d p=%.3f'%(chi,dof,p))
    cl4 = ['unasp','asp','vlfric','voiced']
    M = ctab([(PY[c][2], icls(PY[c][0])) for c in chars], tones, cl4)
    chi, p, dof, _ = chi2_contingency(M); rep('H12', scope, 'tone x initial-class4(unasp,asp,vlfric,voiced)', M.tolist(), 'chi2=%.2f dof=%d p=%.3f'%(chi,dof,p))
    cl3 = lambda i: {'vlfric':'unasp'}.get(icls(i), icls(i))
    M = ctab([(PY[c][2], cl3(PY[c][0])) for c in chars], tones, ['unasp','asp','voiced'])
    chi, p, dof, _ = chi2_contingency(M); rep('H12', scope, 'tone x initial-class3(unasp+fric,asp,voiced)', M.tolist(), 'chi2=%.2f dof=%d p=%.3f'%(chi,dof,p))
    # tone parity (平1,2 vs 仄3,4) x stroke parity
    M = ctab([('ping' if PY[c][2] in (1,2) else 'ze', STROKES[c]%2) for c in chars], ['ping','ze'], [0,1])
    chi, p, dof, _ = chi2_contingency(M); rep('H12', scope, 'ping/ze x stroke-parity', M.tolist(), 'chi2=%.2f p=%.3f'%(chi,p))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results.txt'),'w').write('\n'.join(out))
