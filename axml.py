
import struct,sys,os,json,glob
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def parse_pool(b,off):
    t,hsz,size=u16(b,off),u16(b,off+2),u32(b,off+4)
    sc,stc,flags,sstart,stystart=struct.unpack_from('<IIIII',b,off+8)
    utf8=(flags&(1<<8))!=0
    offs=[u32(b,off+hsz+4*i) for i in range(sc)]
    base=off+sstart; out=[]
    for o in offs:
        p=base+o
        if utf8:
            n=b[p]; p+=1
            if n&0x80: n=((n&0x7f)<<8)|b[p]; p+=1
            nb=b[p]; p+=1
            if nb&0x80: nb=((nb&0x7f)<<8)|b[p]; p+=1
            out.append(b[p:p+nb].decode('utf-8','replace'))
        else:
            n=u16(b,p); p+=2
            if n&0x8000: n=((n&0x7fff)<<16)|u16(b,p); p+=2
            out.append(b[p:p+2*n].decode('utf-16-le','replace'))
    return out

def parse_axml(b):
    t,hsz,size=u16(b,0),u16(b,2),u32(b,4)
    if t!=0x0003: return None
    pool=[]; resmap=[]
    pos=hsz; elems=[]
    while pos<size:
        ct,chs,csz=u16(b,pos),u16(b,pos+2),u32(b,pos+4)
        if csz==0: break
        if ct==0x0001: pool=parse_pool(b,pos)
        elif ct==0x0180:
            n=(csz-chs)//4
            resmap=[u32(b,pos+chs+4*i) for i in range(n)]
        elif ct==0x0102:
            ns=u32(b,pos+chs+0); name=u32(b,pos+chs+4)
            attrStart=u16(b,pos+chs+8); attrSize=u16(b,pos+chs+10); attrCount=u16(b,pos+chs+12)
            ap=pos+chs+attrStart
            attrs=[]
            for i in range(attrCount):
                q=ap+attrSize*i
                ans=u32(b,q); aname=u32(b,q+4); araw=u32(b,q+8)
                vsize=u16(b,q+12); vres0=b[q+14]; vtype=b[q+15]; vdata=u32(b,q+16)
                an=pool[aname] if aname<len(pool) else '?'
                if ans: an='android:'+an
                else:
                    # resolve via resmap if this attr is a framework attr
                    if aname < len(resmap) and resmap[aname]: an='android:'+an
                attrs.append(dict(name=an,type=vtype,data=vdata,raw=pool[araw] if araw<len(pool) else None))
            elems.append(dict(elem=pool[name] if name<len(pool) else '?',attrs=attrs))
        pos+=csz
    return elems

def scan(root,outpath):
    rows=[]
    for p in glob.glob(os.path.join(root,'res','**','*.xml'),recursive=True):
        try:
            b=open(p,'rb').read()
            el=parse_axml(b)
        except Exception as e:
            continue
        if not el: continue
        refs=[]
        for e in el:
            for a in e['attrs']:
                if a['type']==0x01:
                    refs.append((a['name'],a['data']))
        if refs: rows.append(dict(file=os.path.relpath(p,root).replace('\\','/'),refs=refs,elems=[e['elem'] for e in el][:6]))
    json.dump(rows,open(outpath,'w',encoding='utf-8'),ensure_ascii=False)
    print('axml files with refs:',len(rows))
if __name__=='__main__':
    scan(sys.argv[1],sys.argv[2])
