import os
import sys; sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'h1.py')).read().split('rng = np.random')[0])
rng=np.random.default_rng(1); ar=np.arange(N)
for scheme in ['S23','S21']:
    I,F,T=streams(orders['a_text'],scheme); ii,fi,L,LT=build_mats(I,F,scheme); tt=np.array(T)
    r=[LT[ii,fi,tt[rng.permutation(N)]].mean() for _ in range(1000)]
    print(scheme,'tone-only shuffle baseline mean %.4f max %.4f'%(np.mean(r),np.max(r)))
    rr=[]
    for _ in range(1000):
        p=rng.permutation(N); q=rng.permutation(N); rr.append(LT[ii,fi[p],tt[q]].mean())
    print(scheme,'fin+tone indep shuffle baseline mean %.4f max %.4f'%(np.mean(rr),np.max(rr)))
    for oname,order in orders.items():
        I,F,T=streams(order,scheme); ii,fi,L,LT=build_mats(I,F,scheme); tt=np.array(T)
        best=(0,0,0)
        for d in range(1,N):
            fsh=fi[(ar+d)%N]
            for e in range(N):
                v=LT[ii,fsh,tt[(ar+e)%N]].mean()
                if v>best[0]: best=(v,d,e)
        print(' ',oname,scheme,'toned best with d!=0: d=%d e=%d rate=%.4f'%(best[1],best[2],best[0]))
