import numpy as np
from pyulog import ULog
R='/opt/uavv/results/'
out=open(R+'e1b_summary.txt','w')
def inj(d):
    u=ULog(d+'/flight.ulg',['sensor_gps','vehicle_global_position_groundtruth'])
    g=u.get_dataset('sensor_gps').data; t=u.get_dataset('vehicle_global_position_groundtruth').data
    la=np.interp(g['timestamp'],t['timestamp'],t['lat']); lo=np.interp(g['timestamp'],t['timestamp'],t['lon'])
    dl=np.round(g['lat']-la*1e7).astype(np.int64); do=np.round(g['lon']-lo*1e7).astype(np.int64)
    m=(abs(dl)+abs(do))>100
    return g['lat'][m],g['lon'][m]
def best(A,B):
    r=(0.0,-1,0)
    for j in np.where(A[0]==B[0][0])[0]:
        n=min(len(A[0])-j,len(B[0])); f=np.mean((A[0][j:j+n]==B[0][:n])&(A[1][j:j+n]==B[1][:n]))
        if n>=10 and f>r[0]: r=(f,j,n)
    return r
for base in ['RandomValue','FixedNoise']:
    A=inj(R+'gps/%s/seed001'%base)
    for o in [R+'e1/%s_r%d/seed001'%(base,i) for i in range(1,5)]+[R+'gps/%s/seed002'%base]:
        B=inj(o); f,j,n=best(A,B)
        s=len(set(A[0].tolist())&set(B[0].tolist()))
        out.write('%s %s lenA=%d lenB=%d shared_values=%d best_shift=%d match_frac=%.2f n=%d'%(base,o[-17:],len(A[0]),len(B[0]),s,j,f,n)+chr(10))
