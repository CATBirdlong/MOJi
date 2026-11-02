
import os,struct,zipfile,zlib,hashlib
BASE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(BASE)
SRC=os.path.join(ROOT,'build','mojidict-9.1.1-src.apk')
OUT=os.path.join(BASE,'mojidict-9.1.1-final-unsigned.apk')
JS=os.path.join(BASE,'index-cc95ce0f.v53.js'); JS_ENTRY='assets/h5hybrid/assets/index-cc95ce0f.js'
ARSC=os.path.join(BASE,'resources.patched.arsc')
def ru16(b,o): return struct.unpack_from('<H',b,o)[0]
def ru32(b,o): return struct.unpack_from('<I',b,o)[0]
def ruleb(b,o):
    r=0;s=0
    while True:
        x=b[o];o+=1;r|=(x&0x7f)<<s
        if not x&0x80: break
        s+=7
    return r,o
def str_at(b,idx):
    off=ru32(b,ru32(b,0x3c)+4*idx); n,p=ruleb(b,off); end=b.index(b'\x00',p)
    return b[p:end].decode('utf-8','replace')
def type_at(b,i): return str_at(b,ru32(b,ru32(b,0x44)+4*i))
def find_str(b,t):
    for i in range(ru32(b,0x38)):
        if str_at(b,i)==t: return i
def locate(data,cls,meth):
    b=bytearray(data); mo=ru32(b,0x5c); co0=ru32(b,0x64); nm=ru32(b,0x58); nc=ru32(b,0x60)
    tid=None
    for i in range(nm):
        o=mo+8*i
        if type_at(b,ru16(b,o))==cls and str_at(b,ru32(b,o+4))==meth: tid=i; break
    assert tid is not None,(cls,meth)
    off=None
    for ci in range(nc):
        o=co0+32*ci
        if type_at(b,ru32(b,o))!=cls: continue
        q=ru32(b,o+24)
        sf,q=ruleb(b,q); inf,q=ruleb(b,q); dm,q=ruleb(b,q); vm,q=ruleb(b,q)
        for _ in range(sf+inf): _,q=ruleb(b,q); _,q=ruleb(b,q)
        for cnt in (dm,vm):
            prev=0
            for _ in range(cnt):
                dif,q=ruleb(b,q); fl,q=ruleb(b,q); co,q=ruleb(b,q); prev+=dif
                if prev==tid: off=co
            if off: break
        if off: break
    assert off
    return off
def fix_head(b):
    struct.pack_into('<I',b,0x08,0)
    b[0x0c:0x20]=hashlib.sha1(bytes(b[32:])).digest()
    struct.pack_into('<I',b,0x08,zlib.adler32(bytes(b[12:]))&0xffffffff)
def patch(data,cls,meth,body):
    b=bytearray(data); off=locate(b,cls,meth)
    n=ru32(b,off+12); us=off+16
    assert ru16(b,off+6)==0 and len(body)<=n
    struct.pack_into('<%dH'%n,b,us,*([x for x in body]+[0x0000]*(n-len(body))))
    fix_head(b)
    print('  %-26s %-4s units=%-3d %s'%(cls.split('/')[-1],meth,n,' '.join('%04x'%x for x in struct.unpack_from('<%dH'%min(n,6),bytes(b),us))))
    return bytes(b)
def patch_units(data,cls,meth,units):
    """units: list of (index, value) 覆盖"""
    b=bytearray(data); off=locate(b,cls,meth)
    n=ru32(b,off+12); us=off+16
    u=struct.unpack_from('<%dH'%n,b,us)
    for idx,val in units:
        assert idx<n
        struct.pack_into('<H',b,us+2*idx,val)
        print('  unit[%#x] %04x -> %04x  (%s)'%(idx,u[idx],val,cls.split('/')[-1]+'->'+meth))
    fix_head(b)
    return bytes(b)
z=zipfile.ZipFile(SRC); dex2=z.read('classes2.dex'); dex3=z.read('classes3.dex')
si=find_str(bytearray(dex3),'activated')
dex3=patch(dex3,'Lk5/h;','d',[0x001a,si,0x0011])
dex3=patch(dex3,'Lk5/g;','c',[0x1012,0x000f])
ms=4070908800000
dex3=patch(dex3,'Lk5/g;','a',[0x0018]+[(ms>>(16*k))&0xffff for k in range(4)]+[0x0010])
# v5.7(1) 会员叠加：终身标志改回 true
dex3=patch(dex3,'Lcom/mojitec/mojidict/account/b;','c',[0x1012,0x000f])
dex3=patch(dex3,'Lm6/d;','b',[0x1012,0x000f])
dex3=patch(dex3,'Ly5/a;','f',[0x2012,0x000f])
dex2=patch(dex2,'Lcom/google/gson/internal/c;','p',[0x1012,0x000f])
# v5.7(1b) refreshVipCard 跳过终身分支：0x19 if-eqz v2,+88 -> goto +88 (0x5828) + nop
dex3=patch_units(dex3,'Lcom/mojitec/mojidict/ui/fragment/MainMineFragment;','refreshVipCard',[(0x19,0x5828),(0x1a,0x0000)])
# v5.7(3) 背词 A 组上限 10 -> 999
dex3=patch_units(dex3,'Lcom/mojitec/mojidict/ui/ReciteActivity$a;','done',[(0x28,0x03e7)])
dex3=patch_units(dex3,'Lcom/mojitec/mojidict/ui/ReciteFinishActivity$a;','done',[(0x28,0x03e7)])

# v5.8 钱包：getMoCoin/getMoPoint -> 9999
dex3=patch_units(dex3,'Lcom/mojitec/mojidict/ui/fragment/MainMineFragment;','initObserver$lambda$36',
    [(0x09,0x0113),(0x0a,0x270F),(0x0b,0x0000),(0x0c,0x0000),
     (0x17,0x0013),(0x18,0x270F),(0x19,0x0000),(0x1a,0x0000)])

js=open(JS,'rb').read(); arsc=open(ARSC,'rb').read()
patched={'classes2.dex':dex2,'classes3.dex':dex3,JS_ENTRY:js,'resources.arsc':arsc}
with zipfile.ZipFile(SRC) as zz, zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zo:
    for it in zz.infolist():
        data=patched.get(it.filename) or zz.read(it.filename)
        ni=zipfile.ZipInfo(it.filename, date_time=it.date_time)
        ni.compress_type=it.compress_type; ni.external_attr=it.external_attr
        ni.internal_attr=it.internal_attr; ni.create_system=it.create_system
        zo.writestr(ni,data)
print('written',OUT,os.path.getsize(OUT))
