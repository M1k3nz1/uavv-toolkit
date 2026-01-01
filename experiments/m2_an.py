import glob,json,math,numpy as np
from pyulog import ULog
from scipy import stats
R='/opt/uavv/results/'
CEN=(40.2300,-8.4000);M=111320.0;K=M*math.cos(math.radians(CEN[0]))
HL=(CEN[0],CEN[1]-120.0/K)
out=open(R+'m2_summary.txt','w')
def one(d):
    m=json.load(open(d+'/meta.json'))
    u=ULog(d+'/flight.ulg',['vehicle_global_position_groundtruth']); t=u.get_dataset('vehicle_global_position_groundtruth').data
    xt=np.abs(t['lat']-CEN[0])*M
    ed=math.hypot((t['lat'][-1]-HL[0])*M,(t['lon'][-1]-HL[1])*K)
    gain=np.hypot((t['lat']-HL[0])*M,(t['lon']-HL[1])*K).max()
    return m.get('reason')=='disarmed' and ed<15 and gain>100, xt.max(), ed
def wil(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return c-h,c+h
rng=np.random.default_rng(1)
def perm(a,b,N=10000):
    a=np.array(a);b=np.array(b);o=abs(a.mean()-b.mean());z=np.concatenate([a,b]);c=0
    for _ in range(N):
        rng.shuffle(z); c+=abs(z[:len(a)].mean()-z[len(a):].mean())>=o-1e-12
    return (c+1)/(N+1)
D={}
for c in ['gold','FixedNoise','ZigZag','FreezeValue','RandomValue']:
    for d in sorted(glob.glob(R+'m2/%s/seed*'%c)):
        try: D.setdefault(c,[]).append(one(d))
        except Exception as e: out.write('ERR %s %s'%(d,e)+chr(10))
for c,v in D.items():
    n=len(v); k=sum(1 for x in v if x[0]); xt=[x[1] for x in v]; ed=[x[2] for x in v]
    lo,hi=wil(k,n); h=stats.t.ppf(0.975,n-1)*np.std(xt,ddof=1)/math.sqrt(n) if n>1 else float('nan')
    p=perm(xt,[x[1] for x in D['gold']]) if c!='gold' and 'gold' in D else float('nan')
    out.write('%s n=%d completed=%d/%d wilson=[%.2f,%.2f] xtrack=%.1f sd=%.1f ci+-%.1f end_dist=%.1f sd=%.1f p=%.4f'%(c,n,k,n,lo,hi,np.mean(xt),np.std(xt,ddof=1),h,np.mean(ed),np.std(ed,ddof=1),p)+chr(10))
out.close()
