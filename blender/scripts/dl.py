import json,sys,os,subprocess
out=sys.argv[1]
def curl(u,p=None):
    if p:
        os.makedirs(os.path.dirname(p),exist_ok=True)
        if os.path.exists(p): return
        subprocess.run(['curl','-sfL','-o',p,u],check=True)
    else: return subprocess.run(['curl','-sfL',u],check=True,capture_output=True).stdout
for a in sys.argv[2:]:
    d=json.loads(curl(f"https://api.polyhaven.com/files/{a}"))
    g=d['gltf']['1k']['gltf']
    curl(g['url'],f"{out}/{a}/{a}.gltf")
    for rel,f in g['include'].items(): curl(f['url'],f"{out}/{a}/{rel}")
    print('ok',a)
