import json,glob,os,collections
R='/opt/uavv/results/gps'
out=open('/opt/uavv/results/e3_endings.txt','w')
def pr(*a):
    s=' '.join(str(x) for x in a)
    out.write(s+chr(10))
for cfg in ['gold','RandomNoise','DelayValue','RandomValue','FixedNoise']:
    for d in sorted(glob.glob('%s/%s/seed*'%(R,cfg)))[:10]:
        try: m=json.load(open(d+'/meta.json'))
        except Exception: continue
        ev=[(round(e[0]),e[1].strip()) for e in m.get('events',[]) if 'Takeoff' not in e[1]]
        modes=[];st=[];last=None
        for l in open(d+'/telemetry.jsonl'):
            try: j=json.loads(l)
            except Exception: continue
            t=j.get('mavpackettype')
            if t=='HEARTBEAT':
                cm=(j.get('base_mode'),j.get('custom_mode'))
                if cm!=last:
                    modes.append((round(j.get('_t',0)),cm)); last=cm
            if t=='STATUSTEXT': st.append((round(j.get('_t',0)),j.get('text')))
        pr(cfg,os.path.basename(d),'reason',m.get('reason'),'t',round(m.get('t_total',0)))
        pr('  events',ev[:6]); pr('  modes',modes[:8]); pr('  statustext',st[:6])
