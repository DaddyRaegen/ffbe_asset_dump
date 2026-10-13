import struct

def chunks(b):
 off=8
 while off<len(b):
  t,h,s=struct.unpack_from('<HHI',b,off);assert h<=s and off+s<=len(b)
  yield t,b[off:off+s];off+=s
 assert off==len(b)

def strings(c):
 t,h,s=struct.unpack_from('<HHI',c);count,styles,flags,start,style_start=struct.unpack_from('<5I',c,8)
 assert styles==0,'Style-bearing manifest pool requires separate preservation'
 out=[]
 for i in range(count):
  pos=start+struct.unpack_from('<I',c,h+4*i)[0]
  if flags&0x100:
   def length8(p):
    v=c[p];return (((v&127)<<8)|c[p+1],p+2) if v&128 else (v,p+1)
   _,pos=length8(pos);n,pos=length8(pos);out.append(c[pos:pos+n].decode('utf-8'))
  else:
   n=struct.unpack_from('<H',c,pos)[0];pos+=2
   if n&0x8000:n=((n&0x7fff)<<16)|struct.unpack_from('<H',c,pos)[0];pos+=2
   out.append(c[pos:pos+n*2].decode('utf-16-le'))
 return out,flags

def pool(vals,flags):
 data=bytearray();offsets=[]
 def len8(n):return bytes([n]) if n<128 else bytes([(n>>8)|128,n&255])
 for s in vals:
  offsets.append(len(data));b=s.encode('utf-8') if flags&0x100 else s.encode('utf-16-le');n=len(s.encode('utf-16-le'))//2
  if flags&0x100:data.extend(len8(n)+len8(len(b))+b+b'\0')
  else:data.extend(struct.pack('<H',n)+b+b'\0\0')
 while len(data)%4:data.append(0)
 start=28+4*len(vals);size=start+len(data)
 return struct.pack('<HHI5I',1,28,size,len(vals),0,flags,start,0)+struct.pack('<'+'I'*len(offsets),*offsets)+data

def patch_manifest(original,version_code):
 parts=list(chunks(original));sp=next(i for i,(t,c) in enumerate(parts) if t==1);vals,flags=strings(parts[sp][1]);names=list(vals)
 vals.append('O1.GameAssetsBoot');bootstrap=len(vals)-1
 edited=[];activity=None;depth=0;activity_depth=0;insert_at=None;end_activity=None
 for i,(t,c) in enumerate(parts):
  if t==0x102:
   b=bytearray(c);h=struct.unpack_from('<H',c,2)[0];tag=struct.unpack_from('<I',c,h+4)[0];attr_start,attr_size,count=struct.unpack_from('<HHH',c,h+8)
   attrs=[]
   for k in range(count):
    pos=h+attr_start+k*attr_size;ns,name,raw=struct.unpack_from('<III',c,pos);dtype=c[pos+15];value=struct.unpack_from('<I',c,pos+16)[0]
    attrs.append((pos,names[name],dtype,names[value] if dtype==3 else value))
   if names[tag]=='manifest':
    for pos,name,dt,v in attrs:
     if name=='versionCode':assert dt==16 and v==199;struct.pack_into('<I',b,pos+16,version_code);edited.append({'field':'versionCode','before':199,'after':version_code})
    parts[i]=(t,bytes(b))
   if names[tag]=='activity' and any(name=='name' and v in ('com.square_enix.ffbejpn.Lapis','.Lapis') for pos,name,dt,v in attrs):
    assert activity is None
    clone=bytearray(c)
    for pos,name,dt,v in attrs:
     if name=='name':struct.pack_into('<I',clone,pos+8,bootstrap);struct.pack_into('<I',clone,pos+16,bootstrap)
     if name=='exported':assert dt==18;struct.pack_into('<I',clone,pos+16,0)
    activity=bytes(clone);activity_depth=depth
   depth+=1
  elif t==0x103:
   depth-=1;h=struct.unpack_from('<H',c,2)[0];tag=struct.unpack_from('<I',c,h+4)[0]
   if activity is not None and insert_at is None and depth==activity_depth and names[tag]=='activity':insert_at=i+1;end_activity=c
 assert len(edited)==1 and activity and end_activity and insert_at
 parts[sp]=(1,pool(vals,flags));parts[insert_at:insert_at]=[(0x102,activity),(0x103,end_activity)]
 result=b''.join(c for t,c in parts);result=struct.pack('<HHI',3,8,len(result)+8)+result
 return result,edited+[{'field':'new_activity','name':'O1.GameAssetsBoot','exported':False,'existing_activity_and_permissions_preserved':True}]
