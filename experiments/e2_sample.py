import os,time,glob
def pids(name):
    r=[]
    for p in glob.glob('/proc/[0-9]*'):
        try:
            c=open(p+'/cmdline','rb').read().replace(b'\0',b' ')
            if name.encode() in c: r.append(int(p.split('/')[-1]))
        except Exception: pass
    return r
def cpu(p):
    try:
        f=open('/proc/%d/stat'%p).read().rsplit(')',1)[1].split()
        return int(f[11])+int(f[12]), int(f[21])*4096/1e6
    except Exception: return None
CL=os.sysconf('SC_CLK_TCK')
prev={}
out=open('/opt/uavv/logs/e2_cpu.csv','a')
while True:
    t=time.time(); row=[round(t)]
    for n in ('bin/px4','jmavsim_run.jar'):
        tot=0;mem=0
        for p in pids(n):
            c=cpu(p)
            if c is None: continue
            k=(n,p)
            if k in prev: tot+=(c[0]-prev[k][0])/CL/(t-prev[k][2])*100
            prev[k]=(c[0],c[1],t); mem+=c[1]
        row+=[round(tot,1),round(mem)]
    out.write(','.join(map(str,row))+'\n'); out.flush()
    time.sleep(5)
