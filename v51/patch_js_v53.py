
import os,re
base=r'D:\Documents\deepseek-harness\default-workspace\misahre_re'
src=os.path.join(base,'patch','index-cc95ce0f.js')
out=os.path.join(base,'v51','index-cc95ce0f.v53.js')
t=open(src,'rb').read().decode('utf-8','surrogateescape')
def repl(old,newbody,label):
    global t
    i=t.find(old)
    if i<0: print('  MISS',label); return
    pad=len(old)-len(newbody)
    if pad<0: print('  TOOLONG',label); return
    t=t[:i]+newbody+' '*pad+t[i+len(old):]
    print('  OK  %-28s %r -> %r'%(label,old[:46],newbody))
repl('h.subdetails.permissionLimit===-1','!0','subdetails unlimited')
repl('h.examples.permissionLimit===-1','!0','examples unlimited')
repl('e.subdetailsNum=h.subdetails.permissionLimit>0?h.subdetails.permissionLimit:0',
     'e.subdetailsNum=999','subdetailsNum 999')
repl('e.examplesNum=h.examples.permissionLimit>0?h.examples.permissionLimit:0',
     'e.examplesNum=999','examplesNum 999')
open(out,'wb').write(t.encode('utf-8','surrogateescape'))
print('written',out,len(t))
