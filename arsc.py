
import struct, json, sys, io, os

RES_STRING_POOL = 0x0001
RES_TABLE = 0x0002
RES_TABLE_PACKAGE = 0x0200
RES_TABLE_TYPE = 0x0201
RES_TABLE_TYPESPEC = 0x0202
RES_TABLE_LIBRARY = 0x0203

def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]

def parse_pool(b, off):
    t,hsz,size = u16(b,off),u16(b,off+2),u32(b,off+4)
    assert t==RES_STRING_POOL, hex(t)
    sc, stc, flags, sstart, stystart = struct.unpack_from('<IIIII',b,off+8)
    utf8 = (flags & (1<<8)) != 0
    offs = [u32(b, off+hsz+4*i) for i in range(sc)]
    base = off+ sstart
    out=[]
    for o in offs:
        p = base+o
        if utf8:
            # u16 len (chars), then u8 len (bytes) if high bit
            n = b[p]; p+=1
            if n & 0x80:
                n = ((n & 0x7f)<<8) | b[p]; p+=1
            nb = b[p]; p+=1
            if nb & 0x80:
                nb = ((nb & 0x7f)<<8) | b[p]; p+=1
            out.append(b[p:p+nb].decode('utf-8','replace'))
        else:
            n = u16(b,p); p+=2
            if n & 0x8000:
                n = ((n & 0x7fff)<<16) | u16(b,p); p+=2
            out.append(b[p:p+2*n].decode('utf-16-le','replace'))
    return out

def main(path, outdir):
    b = open(path,'rb').read()
    t,hsz,size = u16(b,0),u16(b,2),u32(b,4)
    assert t==RES_TABLE
    pkgcount = u32(b,8)
    pos = hsz
    gpool=[]
    packages=[]
    while pos < size:
        ct,chs,csz = u16(b,pos),u16(b,pos+2),u32(b,pos+4)
        if csz==0: break
        if ct==RES_STRING_POOL:
            gpool = parse_pool(b,pos)
        elif ct==RES_TABLE_PACKAGE:
            pkgid = u32(b,pos+8)
            name = b[pos+12:pos+12+256].decode('utf-16-le','replace').split('\x00')[0]
            typeStringsOff = u32(b,pos+12+256)
            keyStringsOff = u32(b,pos+12+256+4+4+4)  # typeStrings,lastPublicType,keyStrings
            typeStringsOff = u32(b,pos+268)
            lastPublicType = u32(b,pos+272)
            keyStringsOff = u32(b,pos+276)
            lastPublicKey = u32(b,pos+280)
            typeIdOffset = u32(b,pos+284) if chs>=288 else 0
            tpool = parse_pool(b,pos+typeStringsOff)
            kpool = parse_pool(b,pos+keyStringsOff)
            pk = dict(pkgid=pkgid,name=name,typeStrings=tpool,keyStrings=kpool,typeIdOffset=typeIdOffset,entries=[])
            # iterate children
            cpos = pos+chs
            while cpos < pos+csz:
                ct2,ch2,cs2 = u16(b,cpos),u16(b,cpos+2),u32(b,cpos+4)
                if cs2==0: break
                if ct2==RES_TABLE_TYPE:
                    typeId = b[cpos+8]
                    flags = b[cpos+9]
                    entryCount = u32(b,cpos+12)
                    entriesStart = u32(b,cpos+16)
                    cfgSize = u32(b,cpos+20)
                    cfg = b[cpos+20:cpos+20+cfgSize]
                    # decode config: language at offset 8 (2 bytes), country 10, screenLayout etc.
                    lang = cfg[8:10]; country = cfg[10:12]
                    dens = struct.unpack_from('<H',cfg,14)[0] if cfgSize>=16 else 0
                    sdk = struct.unpack_from('<H',cfg,24)[0] if cfgSize>=26 else 0
                    cfgstr = (lang.decode('ascii','replace') if lang[0]!=0 else '')+('-'+country.decode('ascii','replace') if country[0]!=0 else '')
                    if dens: cfgstr += ('|density=%d'%dens)
                    if sdk: cfgstr += ('|sdk=%d'%sdk)
                    if not cfgstr: cfgstr='default'
                    offsArr = cpos+ch2
                    sparse = bool(flags & 0x01)
                    off16 = bool(flags & 0x02)
                    items=[]
                    if sparse:
                        for i in range(entryCount):
                            idx = u16(b,offsArr+4*i); o = u16(b,offsArr+4*i+2)*4
                            items.append((idx,o))
                    elif off16:
                        for i in range(entryCount):
                            o = u16(b,offsArr+2*i)
                            items.append((i, None if o==0xffff else o*4))
                    else:
                        for i in range(entryCount):
                            o = u32(b,offsArr+4*i)
                            items.append((i, None if o==0xffffffff else o))
                    tname = tpool[typeId-1] if 0 < typeId <= len(tpool) else '?'
                    for idx,o in items:
                        if o is None: continue
                        ep = cpos+entriesStart+o
                        esz = u16(b,ep); eflags = u16(b,ep+2); key = u32(b,ep+4)
                        resid = (pkgid<<24) | ((typeId)<<16) | idx
                        keyname = kpool[key] if key < len(kpool) else '?'
                        if eflags & 0x0001:
                            # bag
                            vcnt = u32(b,ep+12)
                            maps=[]
                            mp = ep+esz
                            for m in range(vcnt):
                                mn = u32(b,mp+4*m); mv_size=u16(b,mp+4*m+4); mv_res0=b[mp+4*m+6]; mv_type=b[mp+4*m+7]; mv_data=u32(b,mp+4*m+8)
                                maps.append([mn, mv_type, mv_data])
                            pk['entries'].append(dict(id=resid,packg=name,type=tname,key=keyname,config=cfgstr,complex=True,parent=u32(b,ep+8),maps=maps))
                        else:
                            vp = ep+esz
                            vsize=b[vp]; vres0=b[vp+1]; vtype=b[vp+3]; vdata=u32(b,vp+4)
                            pk['entries'].append(dict(id=resid,packg=name,type=tname,key=keyname,config=cfgstr,complex=False,datatype=vtype,data=vdata))
                cpos += cs2
            packages.append(pk)
        pos += csz
    # resolve strings
    for pk in packages:
        for e in pk['entries']:
            if e.get('complex'):
                e['map']=[[m[0],m[1],m[2],(gpool[m[2]] if m[1]==3 and m[2]<len(gpool) else None)] for m in e['maps']]
            elif e.get('datatype')==3:
                e['value']= gpool[e['data']] if e['data']<len(gpool) else None
    json.dump(dict(gpoolSize=len(gpool), packages=[dict(pkgid=p['pkgid'],name=p['name'],entries=p['entries']) for p in packages], gpool=gpool), open(os.path.join(outdir,'arsc.json'),'w',encoding='utf-8'), ensure_ascii=False)
    print('entries:', sum(len(p['entries']) for p in packages), 'gpool:', len(gpool), 'pkgs:', [p['name'] for p in packages])

main(sys.argv[1], sys.argv[2])
