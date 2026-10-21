import sys, random, itertools
sys.path.insert(0, '/home/user/Decode-Stuff/work')
from data import *
from legal import *
N = len(TEXT); assert N == 230
T = TEXT
HPY = {c: split_py(c, heteronym=True) for c in set(T)}

def leg(a, b, mode='s', tone=None):
    """a=上字 b=下字; mode s=单读音 m=多读音; tone None/'lo'/'up'"""
    ra = [PY[a]] if mode == 's' else HPY[a]
    rb = [PY[b]] if mode == 's' else HPY[b]
    for x in ra:
        for y in rb:
            t = None if tone is None else (y[2] if tone == 'lo' else x[2])
            if is_legal(x[0], y[1], t): return True
    return False

def score(pairs, mode='s', tone=None):
    return sum(leg(T[i], T[j], mode, tone) for i, j in pairs)

def rep(name, pairs):
    n = len(pairs)
    fw = [score(pairs, m, t) for m in 'sm' for t in (None, 'lo', 'up')]
    bw = [score([(j, i) for i, j in pairs], m, t) for m in 'sm' for t in (None, 'lo', 'up')]
    print(f"{name:28s} n={n:3d} 上->下 s:{fw[0]}/{fw[1]}/{fw[2]} m:{fw[3]}/{fw[4]}/{fw[5]} | 下->上 s:{bw[0]}/{bw[1]}/{bw[2]} m:{bw[3]}/{bw[4]}/{bw[5]}  (无调/调下/调上)")
    return fw, bw

R = {}
R['a 相邻(2k,2k+1)'] = [(2*k, 2*k+1) for k in range(115)]
R['b i,i+115'] = [(i, i+115) for i in range(115)]
R['c 镜像 i,229-i'] = [(i, 229-i) for i in range(115)]
R['d 行内左j右j'] = [(10*r+j, 10*r+5+j) for r in range(23) for j in range(5)]
R['e 行内左j右4-j'] = [(10*r+j, 10*r+9-j) for r in range(23) for j in range(5)]
R['f1 行2r与2r+1同列'] = [(10*(2*r)+c, 10*(2*r+1)+c) for r in range(11) for c in range(10)]
R['f2 行r与r+1同列(滑动)'] = [(10*r+c, 10*(r+1)+c) for r in range(22) for c in range(10)]
R['f3 行r与22-r同列'] = [(10*r+c, 10*(22-r)+c) for r in range(11) for c in range(10)]
R['f4 行r与r+1同列(循环23)'] = [(10*r+c, 10*((r+1)%23)+c) for r in range(23) for c in range(10)]
R['x 分句内相邻(0,1)(2,3)'] = [(5*q+j, 5*q+j+1) for q in range(46) for j in (0, 2)]
print("== 固定配对族 ==")
OUT = {}
for k, v in R.items(): OUT[k] = rep(k, v)

print("\n== g: i 与 (i+k) mod 230, 230 对 (上=i) ==")
gs = []
for k in range(1, 230):
    p = [(i, (i+k) % N) for i in range(N)]
    gs.append((score(p), score(p, 'm'), score(p, 's', 'lo'), score(p, 's', 'up'), k))
gs_sorted = sorted(gs, reverse=True)
print("top10 (s无调, m无调, s调下, s调上, k):", gs_sorted[:10])
print("bottom3:", gs_sorted[-3:])
import statistics
print("mean s无调 over k:", statistics.mean(g[0] for g in gs)/230)
# 115-pair version for k: pairs (i, i+k) with i in blocks so disjoint: i in [0..229], (i // k) even  -> only when 230 % (2k)==0
for k in [1,5,23,46,115]:
    if N % (2*k) == 0:
        p = [(i, i+k) for i in range(N) if (i//k) % 2 == 0]
        print(f"disjoint 块配对 k={k}: n={len(p)}", score(p), score([(j,i) for i,j in p]), "m:", score(p,'m'), score([(j,i) for i,j in p],'m'))

print("\n== h: 23x10 网格 列c 与 列c' 同行 ==")
colsc = {}
for c in range(10):
    for d in range(10):
        if c == d: continue
        p = [(10*r+c, 10*r+d) for r in range(23)]
        colsc[(c, d)] = (score(p), score(p, 'm'))
best_cd = sorted(colsc.items(), key=lambda x: -x[1][0])[:8]
print("best ordered (上列,下列):", best_cd)
# best perfect matching of columns (5 pairs, choose best direction per pair)
def matchings(items):
    if not items: yield []; return
    a = items[0]
    for i in range(1, len(items)):
        b = items[i]; rest = items[1:i] + items[i+1:]
        for m in matchings(rest): yield [(a, b)] + m
bestm = None
allm = []
for m in matchings(list(range(10))):
    s = sum(max(colsc[(a, b)][0], colsc[(b, a)][0]) for a, b in m)
    allm.append(s)
    if bestm is None or s > bestm[0]: bestm = (s, m)
print("best column perfect matching (115 对, 每对取较优方向):", bestm, " mean over 945:", statistics.mean(allm))

print("\n== 孤字 ==")
ORPH = [i for i in range(N) if FREQ[T[i]] == 1]
print("孤字数", len(ORPH), "".join(T[i] for i in ORPH))
O = {}
O['i 顺序两两'] = [(ORPH[2*k], ORPH[2*k+1]) for k in range(43)]
O['ii k与k+43'] = [(ORPH[k], ORPH[k+43]) for k in range(43)]
O['iii 镜像 k,85-k'] = [(ORPH[k], ORPH[85-k]) for k in range(43)]
iv = []
for q in range(46):
    oo = [i for i in ORPH if i // 5 == q]
    iv += [(oo[2*k], oo[2*k+1]) for k in range(len(oo)//2)]
O['iv 分句内顺序'] = iv
print("每分句孤字数分布:", Counter(len([i for i in ORPH if i//5 == q]) for q in range(46)))
for k, v in O.items(): OUT[k] = rep(k, v)
# orphan shift scan
og = sorted([(sum(leg(T[ORPH[i]], T[ORPH[(i+k) % 86]]) for i in range(86)), k) for k in range(1, 86)], reverse=True)
print("孤字 shift k 扫描 top5 (/86):", og[:5])

print("\n== 随机基线 2000 次 ==")
rng = random.Random(0)
def baseline(idx, npairs, mode='s', tone=None, n=2000):
    res = []
    for _ in range(n):
        p = idx[:]; rng.shuffle(p)
        res.append(sum(leg(T[p[2*k]], T[p[2*k+1]], mode, tone) for k in range(npairs)) / npairs)
    return statistics.mean(res), max(res), statistics.pstdev(res)
for nm, idx, npr in [('全文230->115', list(range(N)), 115), ('孤字86->43', ORPH, 43)]:
    for mode in 'sm':
        for tone in (None, 'lo', 'up'):
            print(nm, mode, tone, "mean/max/sd = %.3f / %.3f / %.3f" % baseline(idx, npr, mode, tone))

# 全有序对合法率 (上字任意, 下字任意)
allp = sum(leg(a, b) for a in T for b in T) / N**2
print("\n全部 230x230 有序位置对 合法率(s无调): %.3f" % allp)
