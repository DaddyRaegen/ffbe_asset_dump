"""Read only the production ELF symbols/calls; no third-party packages."""
from pathlib import Path
import json,struct

def elf64(blob):
    assert blob[:6]==b'\x7fELF\x02\x01'
    offset=struct.unpack_from('<Q',blob,0x28)[0]
    width,count,names=struct.unpack_from('<HHH',blob,0x3a)
    headers=[struct.unpack_from('<IIQQQQIIQQ',blob,offset+i*width) for i in range(count)]
    strings=blob[headers[names][4]:headers[names][4]+headers[names][5]]
    string=lambda s,i:s[i:s.find(b'\0',i)].decode('utf-8',errors='replace')
    sections={string(strings,h[0]):h for h in headers}
    sy=sections['.dynsym'];st=headers[sy[6]]
    strings=blob[st[4]:st[4]+st[5]]
    symbols=[]
    for pos in range(sy[4],sy[4]+sy[5],sy[9]):
        name,info,other,shndx,address,size=struct.unpack_from('<IBBHQQ',blob,pos)
        symbols.append({'name':string(strings,name),'address':address,'size':size,'section':shndx})
    return headers,sections,symbols

def memory(blob,headers,address,size):
    for h in headers:
        if h[3]<=address and address+size<=h[3]+h[5]:
            return blob[h[4]+address-h[3]:h[4]+address-h[3]+size]
    raise ValueError(hex(address))

def signed(value,bits):
    return value-(1<<bits) if value&(1<<(bits-1)) else value

def calls(blob,headers,sections,symbols,entry):
    names={s['address']:s['name'] for s in symbols if s['address']}
    got={}
    for h in headers:
        if h[1]!=4:continue
        for p in range(h[4],h[4]+h[5],h[9]):
            address,info,_=struct.unpack_from('<QQq',blob,p)
            index=info>>32
            if index:got[address]=symbols[index]['name']
    plt=sections['.plt'];data=blob[plt[4]:plt[4]+plt[5]]
    for i in range(0,len(data)-8,4):
        a,b=struct.unpack_from('<II',data,i)
        if a&0x9f000000==0x90000000 and b&0xffc00000==0xf9400000:
            immediate=signed(((a>>5&0x7ffff)<<2)|(a>>29&3),21)
            address=((plt[3]+i)&~4095)+(immediate<<12)+((b>>10&4095)*8)
            if address in got:names[plt[3]+i]=got[address]
    raw=memory(blob,headers,entry['address'],entry['size'])
    output=[]
    for i in range(0,len(raw)-3,4):
        word=struct.unpack_from('<I',raw,i)[0]
        if word&0xfc000000 in (0x94000000,0x14000000):
            target=entry['address']+i+(signed(word&0x3ffffff,26)<<2)
            if target in names:output.append({'offset':hex(i),'target':names[target]})
    return output

if __name__=='__main__':
    path=Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/source/production-libgame.so')
    blob=path.read_bytes();headers,sections,symbols=elf64(blob)
    selected=[s for s in symbols if s['address'] and s['size'] and
              ('Playback' in s['name']) and any(x in s['name'] for x in ('Book','Chapter','Season','sort'))]
    out=[{**s,'address':hex(s['address']),'calls':calls(blob,headers,sections,symbols,s)} for s in selected]
    target=Path(__file__).with_name('NATIVE_EVENT_SORT_SYMBOLS.json')
    target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{k:v for k,v in s.items() if k!='calls'} for s in out[:250]]))
