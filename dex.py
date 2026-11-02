
import sys,os,json,struct,pickle
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from dexl import Dex,LEN,u16,u32

def main(root,outdir):
    meta=json.load(open(os.path.join(root,'targets.json'),encoding='utf-8'))
    ids=set(meta['ids']); tstr=set(meta['strings'])
    const_hits=[]; str_hits=[]; calls=[]; align_fail=0; units_total=0; nmeth_total=0; nmeth_code=0
    invokes={0x6e,0x6f,0x70,0x71,0x72,0x74,0x75,0x76,0x77,0x78}
    for path in meta['dexs']:
        d=Dex(path); name=os.path.basename(path); b=d.b
        nmeth_total+=d.nmeth
        for cname,mid,co,n,us in d.class_items():
            nmeth_code+=1
            if n==0: continue
            units_total+=n
            cls,mn=d.method(mid)
            u=struct.unpack_from('<%dH'%n,b,us)
            i=0; 
            while i<n:
                x=u[i]; op=x&0xff
                if x==0x0100:
                    if i+1>=n: break
                    i += u[i+1]*2+4; continue
                if x==0x0200:
                    if i+1>=n: break
                    i += u[i+1]*4+2; continue
                if x==0x0300:
                    if i+2>=n: break
                    width=u[i+1]; size=u[i+2]
                    i += 4 + (size*width+1)//2; continue
                l=LEN[op]
                if i+l>n: break
                if op==0x14:
                    val=u[i+1]|(u[i+2]<<16)
                    if val in ids:
                        const_hits.append(dict(dex=name,mid=mid,cls=cls,meth=mn,pc=i,val=val))
                elif op==0x1a:
                    s=d.string(u[i+1])
                    if s in tstr:
                        str_hits.append(dict(dex=name,mid=mid,cls=cls,meth=mn,pc=i,str=s))
                elif op in invokes:
                    calls.append((name,mid,u[i+1]))
                i+=l
            if i!=n: align_fail+=1
    json.dump(dict(const_hits=[dict(h,val=hex(h['val'])) for h in const_hits],string_hits=str_hits,
                   align_fail=align_fail,units=units_total,nmeth=nmeth_total,nmeth_code=nmeth_code),
              open(os.path.join(outdir,'dex_hits.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    pickle.dump(calls,open(os.path.join(outdir,'calls.pkl'),'wb'))
    print('methods',nmeth_total,'with code',nmeth_code,'units',units_total,'align_fail',align_fail)
    print('const_hits',len(const_hits),'string_hits',len(str_hits),'invokes',len(calls))
    for h in const_hits: print('  const',h['val'],h['cls'],h['meth'])
    for h in str_hits: print('  str',h['str'],h['cls'],h['meth'])

if __name__=='__main__':
    main(sys.argv[1],sys.argv[2])
