import os,re,sys
R=os.path.expanduser('~/s26fe/sys17'); C=R+'/config/'; base=R+'/system/system/'+sys.argv[1]
fc=open(C+'system_fs_config').read(); ctx=open(C+'system_file_contexts').read(); a=[];b=[]
for d,ds,fs in [(os.path.dirname(base),[os.path.basename(base)],[])]+list(os.walk(base)):
  for n in ds+fs:
    p=os.path.join(d,n); rel=os.path.relpath(p,R)
    if '\n'+rel+' ' not in fc: a.append(f"{rel} 0 0 {'0755' if os.path.isdir(p) else '0644'}")
    e='/'+re.sub(r'([.+])',r'\\\1',rel)
    if '\n'+e+' ' not in ctx: b.append(e+' u:object_r:system_file:s0')
open(C+'system_fs_config','a').write('\n'+'\n'.join(a)+'\n'); open(C+'system_file_contexts','a').write('\n'+'\n'.join(b)+'\n')
print('added',len(a),len(b))
