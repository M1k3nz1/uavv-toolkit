import json,glob,statistics as S
R=__import__("os").environ.get("UAVV_ROOT", "/opt/uavv")
out=open(R+'/results/e2_timing.txt','w')
for cfg in ['gold','FixedNoise','RandomNoise','ZigZag','DelayValue']:
    for typ in ['ATTITUDE','GLOBAL_POSITION_INT']:
        ds=[]
        for d in sorted(glob.glob(R+'/results/gps/%s/seed*'%cfg))[:10]:
            ts=[]
            for l in open(d+'/telemetry.jsonl'):
                if '"'+typ+'"' not in l[:60]: continue
                try: ts.append(json.loads(l)['_t'])
                except Exception: pass
            ds+=[(b-a)*1000 for a,b in zip(ts,ts[1:])]
        ds.sort()
        out.write('%s %s n=%d mean=%.2f median=%.2f p99=%.2f ms\n'%(cfg,typ,len(ds),S.mean(ds),ds[len(ds)//2],ds[int(len(ds)*0.99)]))
