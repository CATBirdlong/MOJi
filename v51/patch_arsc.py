
import struct,os,json
base=r'D:\Documents\deepseek-harness\default-workspace\misahre_re'
src=os.path.join(base,'build','mojidict-9.1.1-src.apk')
import zipfile
z=zipfile.ZipFile(src)
b=bytearray(z.read('resources.arsc'))
def u16(o): return struct.unpack_from('<H',b,o)[0]
def u32(o): return struct.unpack_from('<I',b,o)[0]
# 定位全局 string pool（第一个 type=1 的 chunk）
pos=u32(4) if False else u16(2)
pos=u16(2)
pool=None
while pos < len(b):
    t=u16(pos); hs=u16(pos+2); sz=u32(pos+4)
    if sz==0: break
    if t==0x0001: pool=pos; break
    pos+=sz
print('string pool at',hex(pool))
sc,stc,flags,sstart,stystart=struct.unpack_from('<IIIII',b,pool+8)
utf8=bool(flags&(1<<8))
print('count',sc,'utf8',utf8)
offs=[u32(pool+hs+4*i) for i in range(sc)]
base_data=pool+sstart
def entry_off(i): return base_data+offs[i]
# 目标串（pool 索引从 arsc.json 拿）
arc=json.load(open(os.path.join(base,'arsc.json'),encoding='utf-8'))
gp=arc['gpool']
def idx_of(s):
    for i,v in enumerate(gp):
        if v==s: return i
    return None
targets=[('积分','积∞'),('积分%1$d','积分∞ ')]
report=[]
for old,new in targets:
    i=idx_of(old)
    if i is None:
        print('未找到',repr(old)); continue
    o=entry_off(i)
    # 解析 utf8 串头
    p=o
    c1=b[p]; p+=1
    if c1&0x80:
        c2=b[p]; p+=1; charlen=((c1&0x7f)<<8)|c2
    else:
        charlen=c1
    b1=b[p]; p+=1
    if b1&0x80:
        b2=b[p]; p+=1; bytelen=((b1&0x7f)<<8)|b2
    else:
        bytelen=b1
    cur=bytes(b[p:p+bytelen]).decode('utf-8','replace')
    print('idx=%-6d 现串=%-12r charlen=%d bytelen=%d'%(i,cur,charlen,bytelen))
    nb=new.encode('utf-8')
    if len(nb)!=bytelen:
        print('   跳过：字节长度不匹配 (%d != %d)'%(len(nb),bytelen)); continue
    if len(new)>charlen:
        print('   跳过：字符数超出'); continue
    if len(new)!=charlen:
        # 改 charlen 前缀（仍 1 字节时）
        if c1&0x80:
            print('   跳过：双字节长度前缀'); continue
        b[o]=len(new)
    b[p:p+bytelen]=nb
    report.append((i,old,new))
print('已替换:',report)
open(os.path.join(base,'v51','resources.patched.arsc'),'wb').write(bytes(b))
print('written arsc',len(b))
