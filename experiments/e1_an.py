import json,math,numpy as np
from pyulog import ULog
R='/opt/uavv/results/'
CEN=(40.212925,-8.4137479); M=111320.0
K=M*math.cos(math.radians(CEN[0]))
out=open(R+'e1_summary.txt','w')
def load(d):
    u=ULog(d+'/flight.ulg',['sensor_gps','vehicle_global_position_groundtruth'])
    g=u.get_dataset('sensor_gps').data; t=u.get_dataset('vehicle_global_position_groundtruth').data
    la=np.interp(g['timestamp'],t['timestamp'],t['lat']); lo=np.interp(g['timestamp'],t['timestamp'],t['lon'])
    dl=np.round(g['lat']-la*1e7).astype(np.int64); do=np.round(g['lon']-lo*1e7).astype(np.int64)
    xt=np.abs(t['lon']-CEN[1])*K
    return g['lat'],g['lon'],dl,do,xt,t['lat'],t['lon']
def act(x):
    m=(abs(x[2])+abs(x[3]))>100
    return [x[i][m][:50] for i in range(4)]
def row(base,d):
    x=load(d); m=json.load(open(d+'/meta.json'))
    hl=CEN[0]-100.0/M
    ed=math.hypot((x[5][-1]-hl)*M,(x[6][-1]-CEN[1])*K)
    return x,'%s %s reason=%s xtrack_max=%.1f end_dist=%.1f'%(base,d.split('/')[-2]+d[-7:],m.get('reason'),x[4].max(),ed)
for base in ['FixedNoise','RandomValue','RandomNoise','AR_A20.0_f10']:
    gps=base!='AR_A20.0_f10'
    ref=R+('gps/%s/seed001'%base if gps else 'imu/%s/seed001'%base)
    others=[R+'e1/%s_r%d/seed001'%(base,i) for i in range(1,5)]
    if gps: others.append(R+'gps/%s/seed002'%base)
    try: A,l=row(base,ref); out.write(l+chr(10))
    except Exception as e: out.write('ERR %s %s'%(ref,e)+chr(10)); continue
    for o in others:
        try: B,l=row(base,o)
        except Exception as e: out.write('ERR %s %s'%(o,e)+chr(10)); continue
        out.write(l)
        if gps:
            a=act(A); b=act(B); n=min(len(a[0]),len(b[0]))
            ea=np.mean((a[0][:n]==b[0][:n])&(a[1][:n]==b[1][:n])); ed=np.mean((a[2][:n]==b[2][:n])&(a[3][:n]==b[3][:n]))
            out.write(' n_active=%d abs_equal=%.2f delta_equal=%.2f'%(n,ea,ed))
        out.write(chr(10))
