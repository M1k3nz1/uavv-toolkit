import glob,json,os,statistics as S
R=__import__("os").environ.get("UAVV_ROOT", "/opt/uavv")
rows=[tuple(map(float,l.split(','))) for l in open(R+'/logs/e2_cpu.csv') if l.count(',')==4]
out=open(R+'/results/e2_cpu.txt','w')
for root,pat in (('imu','results/imu/*/seed*'),('e1','results/e1/*/seed001'),('m2','results/m2/*/seed*')):
    G={}
    for d in glob.glob(R+'/'+pat):
        try:
            end=os.path.getmtime(d+'/meta.json'); a=end-json.load(open(d+'/meta.json')).get('t_total',0)+60
        except Exception: continue
        v=[r for r in rows if a<=r[0]<=end]
        if len(v)<5: continue
        k=(root,'gold' if d.split('/')[-2]=='gold' else 'fault')
        G.setdefault(k,[]).append([S.mean(r[i] for r in v) for i in (1,3,2,4)])
    for k,v in sorted(G.items()):
        m=[S.mean(x[i] for x in v) for i in range(4)]
        out.write('%s %s n=%d px4cpu=%.1f jmavcpu=%.1f px4MB=%.0f jmavMB=%.0f\n'%(k+(len(v),)+tuple(m)))
