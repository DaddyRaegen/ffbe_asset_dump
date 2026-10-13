"""Only replace the qualified build 205 binary versionCode value."""
import struct
def strings(c):
 h=struct.unpack_from('<H',c,2)[0];count,styles,flags,start,style_start=struct.unpack_from('<5I',c,8);assert styles==0
 out=[]
 for i in range(count):
  pos=start+struct.unpack_from('<I',c,h+4*i)[0]
  if flags&0x100:
   def length(p):
    v=c[p];return (((v&127)<<8)|c[p+1],p+2) if v&128 else (v,p+1)
   _,pos=length(pos);n,pos=length(pos);out.append(c[pos:pos+n].decode('utf-8'))
  else:
   n=struct.unpack_from('<H',c,pos)[0];pos+=2
   if n&0x8000:n=((n&0x7fff)<<16)|struct.unpack_from('<H',c,pos)[0];pos+=2
   out.append(c[pos:pos+n*2].decode('utf-16-le'))
 return out
def patch(original,version=206):
 out=bytearray(original);offset=8;names=None;edits=[]
 while offset<len(out):
  t,h,size=struct.unpack_from('<HHI',out,offset);assert h<=size and offset+size<=len(out)
  if t==1:names=strings(out[offset:offset+size])
  if t==0x102:
   assert names;tag=struct.unpack_from('<I',out,offset+h+4)[0]
   if names[tag]=='manifest':
    start,width,count=struct.unpack_from('<HHH',out,offset+h+8)
    for k in range(count):
     p=offset+h+start+k*width;name=struct.unpack_from('<I',out,p+4)[0]
     if names[name]=='versionCode':
      value=struct.unpack_from('<I',out,p+16)[0];assert out[p+15]==16 and value==205
      struct.pack_into('<I',out,p+16,version);edits.append({'offset':p+16,'before':205,'after':version})
  offset+=size
 assert offset==len(out) and len(edits)==1
 return bytes(out),edits
