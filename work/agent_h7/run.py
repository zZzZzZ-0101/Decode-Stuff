import sys; sys.path.insert(0,'/home/user/Decode-Stuff/work')
import numpy as np, itertools, random
from data import TEXT, TIYIN, PY, STROKES
from legal import LEGAL_TONELESS, LEGAL_TONED, I23, F23, split23
rng=np.random.default_rng(1)
N=len(TEXT)
tones=[PY[c][2] for c in TEXT]
print("tone set",sorted(set(tones)))
# alphabets
PINI=['b','p','m','f','d','t','n','l','g','k','h','j','q','x','zh','ch','sh','r','z','c','s','y','w','']
PFIN0="a o e i u v ai ei ui ao ou iu ie ve er an en in un vn ang eng ing ong".split()
PFIN=PFIN0+sorted(f for f in F23 if f not in PFIN0)
need_f={PY[c][1] for c in TEXT}; need_i={PY[c][0] for c in TEXT}
assert need_f<=set(F23) and need_i<=set(I23), (need_f-set(F23), need_i-set(I23))
ALPHS={'L23':(I23,F23),'PIN':(PINI,PFIN)}
stk=lambda c: STROKES[c]
TS=[sum(stk(c) for c in l) for l in TIYIN]; print("tiyin line sums",TS)
S56=[stk(c) for c in "".join(TIYIN)]
TXS=np.array([stk(c) for c in TEXT])

def setup(alph,tmod):
    I,F=ALPHS[alph]; nI,nF=len(I),len(F)
    ci=np.array([I.index(PY[c][0]) for c in TEXT]); cf=np.array([F.index(PY[c][1]) for c in TEXT])
    ct=np.array([t-1 for t in tones])
    LIF=np.zeros((nI,nF),bool); LIFT=np.zeros((nI,nF,5),bool)
    for s,t in LEGAL_TONED:
        a,b=split23(s)
        if a in I and b in F: LIF[I.index(a),F.index(b)]=True; LIFT[I.index(a),F.index(b),t-1]=True
    return nI,nF,ci,cf,ct,LIF,LIFT

def seqs(ci,cf,ct,nI,nF,tmod):
    out={'fwd':(ci,cf,ct),'rev':(ci[::-1],cf[::-1],ct[::-1])}
    d=lambda x,n: np.concatenate([[x[0]],(x[1:]-x[:-1])%n])
    out['diff']=(d(ci,nI),d(cf,nF),d(ct,tmod) if tmod==5 or ct.max()<4 else ct)
    return out

COMPS=['I','F','IF','IFT','gridIF','gridIFT']
def decode(K,ci,cf,ct,nI,nF,tmod,comp,sign):
    # K: array (...,N) ; returns toneless legal mask and toned legal mask components
    k=sign*K
    i,f,t=ci+0*k,cf+0*k,ct+0*k
    if comp=='I': i=(ci-k)%nI
    elif comp=='F': f=(cf-k)%nF
    elif comp=='IF': i=(ci-k)%nI; f=(cf-k)%nF
    elif comp=='IFT': i=(ci-k)%nI; f=(cf-k)%nF; t=(ct-k)%tmod
    elif comp=='gridIF':
        g=(ci*nF+cf-k)%(nI*nF); i,f=g//nF,g%nF
    elif comp=='gridIFT':
        g=((ci*nF+cf)*tmod+ct-k)%(nI*nF*tmod); t=g%tmod; g//=tmod; i,f=g//nF,g%nF
    return i,f,t

def score(i,f,t,LIF,LIFT):
    a=LIF[i,f].mean(-1); b=LIFT[i,f,np.minimum(t,4)].mean(-1)
    return a,b

# key builders: return dict name-> array (M,N)
pos=np.arange(N)
def periodic(vals,mode):
    idx={'pos':pos,'row':pos//10,'clause':pos//5}[mode]
    return np.array(vals)[idx%len(vals)]
keys={}
for m in ['pos','row','clause']:
    keys[f'H11_{m}']=periodic(TS,m)[None]
S56a=np.array(S56)
for dr,arr in [('f',S56a),('r',S56a[::-1])]:
    keys[f'H7_{dr}']=np.array([arr[(o+pos)%56] for o in range(56)])
prevk=np.concatenate([[0],TXS[:-1]]); prevc=np.roll(TXS,1); nextk=np.concatenate([TXS[1:],[0]]); nextc=np.roll(TXS,-1)
keys['H9_prev0']=prevk[None]; keys['H9_prevcyc']=prevc[None]; keys['H9_next0']=nextk[None]; keys['H9_nextcyc']=nextc[None]
keys['H10_self']=TXS[None]

results=[]
allstk=np.array(list(TXS)+S56)
for alph in ALPHS:
  for tmod in [4,5]:
    nI,nF,ci0,cf0,ct0,LIF,LIFT=setup(alph,tmod)
    for sq,(ci,cf,ct) in seqs(ci0,cf0,ct0,nI,nF,tmod).items():
      for comp in COMPS:
        if tmod==5 and comp not in ('IFT','gridIFT'): continue
        for sign in [1,-1]:
          cfg=(alph,tmod,sq,comp,'-' if sign==1 else '+')
          # random baseline
          R=rng.choice(allstk,size=(2000,N))
          a,b=score(*decode(R,ci,cf,ct,nI,nF,tmod,comp,sign),LIF,LIFT)
          base=(a.mean(),a.max(),b.mean(),b.max())
          # random periodic-8
          R8=rng.choice(allstk,size=(2000,8))[:,pos%8]
          a8,b8=score(*decode(R8,ci,cf,ct,nI,nF,tmod,comp,sign),LIF,LIFT)
          for kn,K in keys.items():
            a,b=score(*decode(K,ci,cf,ct,nI,nF,tmod,comp,sign),LIF,LIFT)
            j=int(np.argmax(a+b*1e-3))
            results.append((a[j],b[j],kn+(f'_o{j}' if K.shape[0]>1 else ''),cfg,base))
          # H8: per residue class, choose char from tiyin line m
          for m in ['pos','row','clause']:
            idx={'pos':pos,'row':pos//10,'clause':pos//5}[m]%8
            besta=0;bestb=0;nfull=1;pick=[]
            for r in range(8):
              msk=idx==r
              opts=[]
              for ch in TIYIN[r]:
                K=np.full(N,stk(ch))
                ii,ff,tt=decode(K,ci,cf,ct,nI,nF,tmod,comp,sign)
                la=LIF[ii,ff][msk].sum(); lb=LIFT[ii,ff,np.minimum(tt,4)][msk].sum()
                opts.append((la,lb,ch))
              o=max(opts); besta+=o[0]; bestb+=o[1]; pick.append(o[2])
              nfull*=sum(1 for x in opts if x[0]==msk.sum())
            results.append((besta/N,bestb/N,f'H8_{m}_best[{"".join(pick)}] n100%={nfull}',cfg,base))
          # optimized random baseline for H8 (pos): 200 random 7x8 grids
          idx=pos%8; bb=[]
          for _ in range(200):
            tot=0
            for r in range(8):
              msk=idx==r
              tot+=max(LIF[tuple(decode(np.full(N,v),ci,cf,ct,nI,nF,tmod,comp,sign)[:2])][msk].sum() for v in rng.choice(allstk,7))
            bb.append(tot/N)
          results[-3]=results[-3][:4]+(base+(np.mean(bb),np.max(bb),a8.mean(),a8.max()),)
          for q in (-2,-1): results[q]=results[q][:4]+(base+(np.mean(bb),np.max(bb),a8.mean(),a8.max()),)
results.sort(key=lambda r:(-r[0],-r[1]))
import pickle; pickle.dump(results,open('/home/user/Decode-Stuff/work/agent_h7/results.pkl','wb'))
print("TOP 25 by toneless")
for r in results[:25]:
    print(f"{r[0]:.4f} {r[1]:.4f} {r[2]} {r[3]} base(mean/max toneless={r[4][0]:.3f}/{r[4][1]:.3f} toned={r[4][2]:.3f}/{r[4][3]:.3f})" + (f" H8optbase={r[4][4]:.3f}/{r[4][5]:.3f} per8={r[4][6]:.3f}/{r[4][7]:.3f}" if len(r[4])>4 else ""))
print("TOP 10 by toned")
for r in sorted(results,key=lambda r:-r[1])[:10]:
    print(f"{r[0]:.4f} {r[1]:.4f} {r[2]} {r[3]} base={r[4][2]:.3f}/{r[4][3]:.3f}")
print("count 100% toneless:",sum(r[0]==1 for r in results), "total",len(results))
