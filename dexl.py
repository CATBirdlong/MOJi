
import struct,os,json,collections

def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def uleb(b,o):
    r=0;s=0
    while True:
        x=b[o];o+=1; r|=(x&0x7f)<<s
        if not (x&0x80): break
        s+=7
    return r,o
def sleb(b,o):
    r=0;s=0
    while True:
        x=b[o];o+=1; r|=(x&0x7f)<<s; s+=7
        if not (x&0x80):
            if s<32 and (x&0x40): r|=-(1<<s)
            break
    return r,o
def read_mutf8(b,o):
    n,o=uleb(b,o); end=b.index(b'\x00',o); return b[o:end].decode('utf-8','replace'),end+1

LEN=[1]*256
for op in range(0x00,0x1c): LEN[op]=1
LEN[0x02]=2;LEN[0x03]=3;LEN[0x05]=2;LEN[0x06]=3;LEN[0x08]=2;LEN[0x09]=3
LEN[0x13]=2;LEN[0x14]=3;LEN[0x15]=2;LEN[0x16]=2;LEN[0x17]=3;LEN[0x18]=5;LEN[0x19]=2
LEN[0x1a]=2;LEN[0x1b]=3;LEN[0x1c]=2
LEN[0x1f]=2;LEN[0x20]=2;LEN[0x22]=2;LEN[0x23]=2;LEN[0x24]=3;LEN[0x25]=3;LEN[0x26]=3
LEN[0x29]=2;LEN[0x2a]=3;LEN[0x2b]=3;LEN[0x2c]=3
for op in range(0x2d,0x3e): LEN[op]=2
for op in range(0x52,0x6e): LEN[op]=2
for op in range(0x6e,0x73): LEN[op]=3
for op in range(0x74,0x79): LEN[op]=3
for op in range(0x90,0xb0): LEN[op]=2
for op in range(0xd0,0xd8): LEN[op]=2
for op in range(0xd8,0xe3): LEN[op]=2
LEN[0xfa]=4;LEN[0xfb]=4;LEN[0xfc]=3;LEN[0xfd]=3;LEN[0xfe]=2;LEN[0xff]=2

class Dex:
    def __init__(s,p):
        s.p=p; s.b=b=open(p,'rb').read()
        s.nstr=u32(b,0x38);s.str_off=u32(b,0x3c)
        s.type_off=u32(b,0x44)
        s.nmeth=u32(b,0x58);s.meth_off=u32(b,0x5c)
        s.nclass=u32(b,0x60);s.class_off=u32(b,0x64)
        s._s={}
    def string(s,i):
        v=s._s.get(i)
        if v is None:
            v,_=read_mutf8(s.b,u32(s.b,s.str_off+4*i)); s._s[i]=v
        return v
    def type(s,i): return s.string(u32(s.b,s.type_off+4*i))
    def method(s,i):
        o=s.meth_off+8*i; return s.type(u16(s.b,o)), s.string(u32(s.b,o+4))
    def fields(s):
        nf=u32(s.b,0x50); off=u32(s.b,0x54); out=[]
        for i in range(nf):
            o=off+8*i
            out.append((s.type(u16(s.b,o)), s.type(u16(s.b,o+2)), s.string(u32(s.b,o+4))))
        return out
    def methods(s):
        out=[]
        for i in range(s.nmeth):
            cl,mn=s.method(i); out.append((cl,mn))
        return out
    def class_items(s):
        """yield (class_name, mid, code_off, n_units, insns_off) for every method with code"""
        b=s.b
        for ci in range(s.nclass):
            o=s.class_off+32*ci
            cname=s.type(u32(b,o))
            cd=u32(b,o+24)
            if cd==0: continue
            q=cd
            sf,q=uleb(b,q);inf,q=uleb(b,q);dm,q=uleb(b,q);vm,q=uleb(b,q)
            for _ in range(sf+inf):
                _,q=uleb(b,q);_,q=uleb(b,q)
            for cnt in (dm,vm):
                prev=0
                for _ in range(cnt):
                    dif,q=uleb(b,q);fl,q=uleb(b,q);co,q=uleb(b,q)
                    prev+=dif
                    if co==0: continue
                    n=u32(b,co+12)
                    yield cname, prev, co, n, co+16
    def code_ranges(s):
        rs=[]
        for cname,mid,co,n,us in s.class_items():
            rs.append((us,us+2*n,mid))
        rs.sort()
        return rs
