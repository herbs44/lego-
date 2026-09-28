import os,sys,urllib.request,urllib.error,functools
C=os.path.join(os.path.dirname(os.path.abspath(__file__)),'cache')
os.makedirs(C,exist_ok=True)
UP='https://raw.githubusercontent.com/gkjohnson/ldraw-parts-library/master/complete/ldraw/'
def get(rel):
    rel=rel.lower(); cf=os.path.join(C,rel.replace('/','__'))
    if os.path.exists(cf): return open(cf,'rb').read().decode('utf8','replace')
    if os.path.exists(cf+'.404'): return None
    for attempt in range(4):
        try: b=urllib.request.urlopen(UP+rel,timeout=30).read(); break
        except urllib.error.HTTPError as e:
            if e.code==404: open(cf+'.404','w').close(); return None
        except Exception: pass
    else: raise IOError('fetch failed '+rel)
    open(cf,'wb').write(b); return b.decode('utf8','replace')
def find(name):
    name=name.replace('\\','/').lower()
    for pre in ('parts/','p/','parts/s/','p/48/'):
        t=get(pre+name)
        if t is not None: return t
    raise KeyError(name)
def mul(A,B):
    return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
@functools.lru_cache(None)
def pts(name):
    out=[]
    for L in find(name).splitlines():
        p=L.split()
        if not p: continue
        if p[0]=='1':
            x,y,z=map(float,p[2:5]); M=[list(map(float,p[5:8])),list(map(float,p[8:11])),list(map(float,p[11:14]))]
            for (a,b,c) in pts(' '.join(p[14:])):
                out.append((x+M[0][0]*a+M[0][1]*b+M[0][2]*c, y+M[1][0]*a+M[1][1]*b+M[1][2]*c, z+M[2][0]*a+M[2][1]*b+M[2][2]*c))
        elif p[0] in '34':
            v=list(map(float,p[2:])); out+= [tuple(v[i:i+3]) for i in range(0,len(v),3)]
    # reduce
    if not out: return tuple()
    xs=[q[0] for q in out];ys=[q[1] for q in out];zs=[q[2] for q in out]
    return tuple(set(out)) if len(out)<3000 else tuple(set(out))
def bbox(name):
    P=pts(name); xs=[q[0] for q in P];ys=[q[1] for q in P];zs=[q[2] for q in P]
    return (round(min(xs),1),round(max(xs),1)),(round(min(ys),1),round(max(ys),1)),(round(min(zs),1),round(max(zs),1))
if __name__=='__main__':
    for n in sys.argv[1:]:
        try:
            t=find(n+'.dat'); print(n, t.splitlines()[0][2:], bbox(n+'.dat'))
        except Exception as e: print(n,'MISSING',e)
