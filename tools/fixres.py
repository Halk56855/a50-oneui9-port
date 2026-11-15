import sys, struct, zlib, shutil, os
apk=sys.argv[1]; want=dict(a.split('=',1) for a in sys.argv[2:])
d=bytearray(open(apk,'rb').read())
eocd=d.rfind(b'PK\x05\x06'); cd_size,cd_off=struct.unpack_from('<II',d,eocd+12)
ents=[]; p=cd_off
while p<cd_off+cd_size:
    fl,meth,_,_,crc,cs,us,nl,el,cl=struct.unpack_from('<HHHHIIIHHH',d,p+8)
    ents.append(dict(cdp=p,name=bytes(d[p+46:p+46+nl]),lho=struct.unpack_from('<I',d,p+42)[0],meth=meth,fl=fl,cs=cs)); p+=46+nl+el+cl
a=[e for e in ents if e['name']==b'resources.arsc'][0]; assert a['meth']==0 and not a['fl']&8
lh=a['lho']; nl,el=struct.unpack_from('<HH',d,lh+26); ds=lh+30+nl+el; de=ds+a['cs']
A=bytearray(d[ds:de])
def pool_read(buf,sp,i):
    st,shs,ssz,cnt,scnt,flg,sstart,stys=struct.unpack_from('<HHIIIIII',buf,sp)
    o=sp+sstart+struct.unpack_from('<I',buf,sp+shs+4*i)[0]
    if flg&0x100:
        n=buf[o]; o+=2 if n&0x80 else 1
        n=buf[o]
        if n&0x80: n=((n&0x7f)<<8)|buf[o+1]; o+=2
        else: o+=1
        return bytes(buf[o:o+n]).decode('utf-8','replace')
    n=struct.unpack_from('<H',buf,o)[0]; o+=2
    if n&0x8000: n=((n&0x7fff)<<16)|struct.unpack_from('<H',buf,o)[0]; o+=2
    return bytes(buf[o:o+2*n]).decode('utf-16le','replace')
def pool_count(buf,sp): return struct.unpack_from('<I',buf,sp+8)[0]
t,hs,tsz,pc=struct.unpack_from('<HHII',A,0); assert t==2
gp=hs; gsize=struct.unpack_from('<I',A,gp+4)[0]
targets={}; p=gp+gsize
while p<len(A):
    ct,chs,csz=struct.unpack_from('<HHI',A,p)
    if ct==0x200:
        pid=struct.unpack_from('<I',A,p+8)[0]
        ts,_,ks=struct.unpack_from('<III',A,p+268); tsp,ksp=p+ts,p+ks
        tnames=[pool_read(A,tsp,i) for i in range(pool_count(A,tsp))]
        keyidx={}
        for i in range(pool_count(A,ksp)):
            k=pool_read(A,ksp,i)
            if k in want: keyidx[i]=k
        q=p+chs
        while q<p+csz:
            qt,qhs,qsz=struct.unpack_from('<HHI',A,q)
            if qt==0x201 and pid==1:
                tid,tfl,_,ecnt,estart=struct.unpack_from('<BBHII',A,q+8)
                if tnames[tid-1]=='string':
                    eo=q+qhs; pairs=[]
                    if tfl&1:
                        for j in range(ecnt): pairs.append(struct.unpack_from('<HH',A,eo+4*j)[1]*4)
                    elif tfl&2:
                        for j in range(ecnt):
                            v=struct.unpack_from('<H',A,eo+2*j)[0]
                            if v!=0xffff: pairs.append(v*4)
                    else:
                        for j in range(ecnt):
                            v=struct.unpack_from('<I',A,eo+4*j)[0]
                            if v!=0xffffffff: pairs.append(v)
                    for off in pairs:
                        e=q+estart+off; esz,efl=struct.unpack_from('<HH',A,e)
                        if efl&0x8: key=esz; dtype=efl>>8; dpos=e+4
                        else:
                            if efl&1: continue
                            key=struct.unpack_from('<I',A,e+4)[0]; dtype=A[e+11]; dpos=e+12
                        if key in keyidx and dtype==0x03: targets.setdefault(keyidx[key],[]).append(dpos)
            q+=qsz
    p+=csz
for n in want:
    if n not in targets: sys.exit(f"!! resource {n} not found - nothing changed")
st,shs,ssz,cnt,scnt,flg,sstart,stys=struct.unpack_from('<HHIIIIII',A,gp)
utf8=bool(flg&0x100); blob=b''; newidx={}
vals=list(dict.fromkeys(want.values())); k=len(vals); rel=[]
for v in vals:
    b=v.encode(); assert len(b)<128
    s=bytes([len(v),len(b)])+b+b'\0' if utf8 else struct.pack('<H',len(v))+v.encode('utf-16le')+b'\0\0'
    rel.append(len(blob)); blob+=s
blob+=b'\0'*((-len(blob))%4)
datalen=(stys if scnt else ssz)-sstart
ins_data=gp+(stys if scnt else ssz); ins_offs=gp+shs+4*cnt
for i,v in enumerate(vals): newidx[v]=cnt+i
A[ins_data:ins_data]=blob
A[ins_offs:ins_offs]=b''.join(struct.pack('<I',datalen+r) for r in rel)
g=len(blob)+4*k
for n,lst in targets.items():
    for dpos in lst: struct.pack_into('<I',A,dpos+(g if dpos>gp else 0),newidx[want[n]])
struct.pack_into('<IIIII',A,gp+4,ssz+g,cnt+k,scnt,flg,sstart+4*k)
if scnt: struct.pack_into('<I',A,gp+24,stys+g)
struct.pack_into('<I',A,4,tsz+g)
for v in vals: assert pool_read(A,gp,newidx[v])==v
crc=zlib.crc32(A)&0xffffffff; L=len(A); dl=L-a['cs']
struct.pack_into('<III',d,lh+14,crc,L,L); struct.pack_into('<III',d,a['cdp']+16,crc,L,L)
for e in ents:
    if e['lho']>lh: struct.pack_into('<I',d,e['cdp']+42,e['lho']+dl)
struct.pack_into('<I',d,eocd+16,cd_off+dl)
n=1
while os.path.exists(os.path.expanduser(f'~/framework-res.apk.bak_{n}')): n+=1
shutil.copy2(apk,os.path.expanduser(f'~/framework-res.apk.bak_{n}'))
open(apk,'wb').write(d[:ds]+A+d[de:])
for nme,lst in targets.items(): print(f"SET {nme} = {want[nme]}  ({len(lst)} config(s))")
print(f"+{dl} bytes, backup ~/framework-res.apk.bak_{n}")
