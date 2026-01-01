import subprocess,time,json
R=__import__("os").environ.get("UAVV_ROOT", "/opt/uavv")
X=R+'/experiments/'
g={}
exec(open(X+'campaign.py').read().split('OK =')[0],g)
CF=g['CFGS']
LOG=open(R+'/logs/queue_e.log','a')
OKR=('disarmed','timeout')
def busy():
    return subprocess.run(['pgrep','-f','campaign'],capture_output=True,text=True).stdout.strip()!=''
def trial(script,root,cfg,seed,args):
    out='%s/results/%s/%s/seed%03d'%(R,root,cfg,seed)
    for att in range(3):
        try:
            if json.load(open(out+'/meta.json')).get('reason') in OKR: return
        except Exception: pass
        t=time.time()
        r=subprocess.run(['python3',X+script,'--seed',str(seed),'--cfg',cfg]+args,capture_output=True,text=True,cwd=X)
        LOG.write('%s %s s%d try%d %.0fs %s\n'%(root,cfg,seed,att,time.time()-t,(r.stdout.strip().splitlines() or ['?'])[-1])); LOG.flush()
while busy(): time.sleep(30)
LOG.write('QUEUE START\n'); LOG.flush()
for rep in range(1,5):
    for name in ('FixedNoise','RandomValue','RandomNoise'):
        sub,v=CF[name]
        trial('runtrial_e1.py','e1',name+'_r%d'%rep,1,['--sub',sub,'--values',v])
    trial('runtrial_imu_e1.py','e1','AR_A20.0_f10_r%d'%rep,1,['--sub','AcousticResonance','--values','20.0, 10, 0, 0','--tstart','100','--tend','1000'])
LOG.write('E1 DONE\n'); LOG.flush()
for seed in range(1,11):
    for name in ('gold','FixedNoise','ZigZag','FreezeValue','RandomValue'):
        if name=='gold': a=['--gold']
        else:
            sub,v=CF[name]; a=['--sub',sub,'--values',v]
        trial('runtrial_m2.py','m2',name,seed,a+['--timeout','300'])
LOG.write('E5 DONE\n'); LOG.close()
