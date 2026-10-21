import sys; sys.path.insert(0,'/home/user/Decode-Stuff/work'); sys.argv=['x']
exec(open('h3.py').read().split('print("== 固定配对族 ==")')[0])
p = [(2*k, 2*k+1) for k in range(115)]
bad = [(T[i]+T[j], PY[T[i]][0]+'+'+PY[T[j]][1]) for i,j in p if not leg(T[i],T[j])]
badm = [(T[i]+T[j], PY[T[i]][0]+'+'+PY[T[j]][1]) for i,j in p if not leg(T[i],T[j],'m')]
print("a 上->下 single 不合法", len(bad), bad)
print("a 上->下 multi 不合法", len(badm), badm)
# cross-clause vs within
cross = [(i,j) for i,j in p if i//5 != j//5]
print("a cross-clause pairs", len(cross), sum(leg(T[i],T[j]) for i,j in cross))
# shift k=1 within clause vs crossing
w = [(i,i+1) for i in range(229) if i//5==(i+1)//5]; c=[(i,i+1) for i in range(229) if i//5!=(i+1)//5]
print("k=1 within", len(w), sum(leg(T[i],T[j]) for i,j in w), "cross", len(c), sum(leg(T[i],T[j]) for i,j in c))
# odd offset adjacency (2k+1,2k+2)
q=[(2*k+1,2*k+2) for k in range(114)]
print("错位相邻 (2k+1,2k+2)", len(q), sum(leg(T[i],T[j]) for i,j in q))
# 同字频 baseline: shuffle positions but keep cross/within? simple permutation test on k=1 score
import random,statistics
rng=random.Random(1); arr=list(T); sc=[]
for _ in range(2000):
    rng.shuffle(arr); sc.append(sum(leg(arr[i],arr[i+1]) for i in range(229)))
print("k=1 (229对) 打乱文本基线 mean/max/sd", statistics.mean(sc), max(sc), statistics.pstdev(sc), "实测", sum(leg(T[i],T[i+1]) for i in range(229)))
