
import sys,os,json,struct,pickle,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from dexl import Dex,u16,u32

meta=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'targets.json'),encoding='utf-8'))
dexs=[Dex(p) for p in meta['dexs']]; names=[os.path.basename(p) for p in meta['dexs']]
D=dict(zip(names,dexs))
def gm(dn,mid):
    d=D[dn]
    if mid>=d.nmeth: return '?'
    cl,mn=d.method(mid); return cl+'->'+mn
ranges={}
for n,d in zip(names,dexs): ranges[n]=d.code_ranges()
def attr_at(dn,off):
    rs=ranges[dn]; lo,hi=0,len(rs)-1
    while lo<=hi:
        m=(lo+hi)//2; s,e,mid=rs[m]
        if off<s: hi=m-1
        elif off>=e: lo=m+1
        else: return mid,off-s
    return None,None
ids=meta['ids']
print('=== 4-byte LE occurrences (cross-check) ===')
rawhits=[]
for v in ids:
    pat=struct.pack('<I',v)
    print(hex(v))
    for n in names:
        b=D[n].b; start=0
        while True:
            i=b.find(pat,start)
            if i<0: break
            start=i+1
            mid,o=attr_at(n,i)
            if mid is not None:
                print('   %s @%#x -> %s pc=%d'%(n,i,gm(n,mid),o//2))
                rawhits.append((v,n,mid,o//2))
            else:
                print('   %s @%#x -> (non-code data)'%(n,i))
print()
calls=pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'calls.pkl'),'rb'))
callers=collections.defaultdict(list)
for dn,cl,ce in calls: callers[(dn,ce)].append((dn,cl))
print('=== caller chains (depth 4) ===')
seen_global=set()
def show(dn,mid,depth,prefix,visited):
    if depth<0: return
    cs=[x for x in callers.get((dn,mid),[]) if x not in visited]
    for i,(cn,cm) in enumerate(cs[:5]):
        last = (i==len(cs[:5])-1)
        print(prefix+('└─ ' if last else '├─ ')+gm(cn,cm)+('   [%d callers]'%len(callers.get((cn,cm),[]))))
        show(cn,cm,depth-1,prefix+('   ' if last else '│  '),visited|{(dn,mid)})
for v,n,mid,pc in dict.fromkeys(rawhits):
    print('%s  %s  pc=%d'%(hex(v),gm(n,mid),pc))
    show(n,mid,3,'  ',{(n,mid)})
    print()
