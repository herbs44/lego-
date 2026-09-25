import sys, ldbbox as L
from concurrent.futures import ThreadPoolExecutor
seen=set()
def refs(text):
    out=[]
    for line in text.splitlines():
        p=line.split()
        if p and p[0]=='1' and len(p)>=15: out.append(' '.join(p[14:]).replace('\\','/').lower())
    return out
mpd=open(sys.argv[1]).read()
local={l.split(None,2)[2].strip().lower() for l in mpd.splitlines() if l.startswith('0 FILE')}
todo=[r for r in refs(mpd) if r not in local]
L.get('LDConfig.ldr')
with ThreadPoolExecutor(8) as ex:
    while todo:
        batch=[t for t in set(todo) if t not in seen]; seen|=set(batch); todo=[]
        for t,txt in zip(batch, ex.map(lambda n: L.find(n), batch)):
            todo+=refs(txt)
print('files',len(seen))
