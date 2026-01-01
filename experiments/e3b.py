import json,glob,os,math
R='/opt/uavv/results/gps'
CEN=(40.212925,-8.4137479); M=111320.0
home=(CEN[0]-100.0/M,CEN[1])
rows=[]
for cfg in ['gold','RandomNoise','DelayValue','RandomValue','FixedNoise','FreezeValue']:
    for d in sorted(glob.glob('%s/%s/seed*'%(R,cfg)))[:10]:
        try: m=json.load(open(d+'/meta.json'))
        except Exception: continue
        seq=-1;alt=0;mx=0;la=lo=None;nm=0;last=None;ns=0;tl=0
        for l in open(d+'/telemetry.jsonl'):
            try: j=json.loads(l)
            except Exception: continue
            t=j.get('mavpackettype')
            if t=='MISSION_CURRENT': seq=j.get('seq',seq)
            if t=='GLOBAL_POSITION_INT':
                la=j['lat']/1e7;lo=j['lon']/1e7;alt=j['relative_alt']/1000.0;mx=max(mx,alt);tl=j.get('_t',tl)
            if t=='HEARTBEAT':
                cm=j.get('custom_mode')
                if cm!=last: nm+=1;last=cm
            if t=='STATUSTEXT': ns+=1
        dist=-1 if la is None else math.hypot((la-home[0])*M,(lo-home[1])*M*math.cos(math.radians(CEN[0])))
        rows.append((cfg,os.path.basename(d)[-3:],m.get('reason'),round(m.get('t_total',0)),seq,round(mx,1),round(alt,1),round(dist,1),nm,ns))
o=open('/opt/uavv/results/e3b.csv','w')
o.write('cfg,seed,reason,t,lastseq,maxalt,finalalt,finaldist,nmodes,nstatus'+chr(10))
for r in rows: o.write(','.join(map(str,r))+chr(10))
pyth
