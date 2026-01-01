R=__import__("os").environ.get("UAVV_ROOT", "/opt/uavv")
X=R+'/experiments/'
def mk(src,dst,subs):
    s=open(X+src).read()
    for a,b in subs:
        assert a in s,a
        s=s.replace(a,b)
    open(X+dst,'w').write(s)
mk('runtrial.py','runtrial_e1.py',[('/results/gps/','/results/e1/')])
mk('runtrial_imu.py','runtrial_imu_e1.py',[('/results/imu/','/results/e1/')])
C='math.cos(math.radians(CEN[0]))'
mk('runtrial.py','runtrial_m2.py',[('/results/gps/','/results/m2/'),
 ('CEN = (40.212925, -8.4137479)','import math\nCEN = (40.2300, -8.4000)'),
 ('home = (CEN[0] - 100.0 / M, CEN[1])','home = (CEN[0], CEN[1] - 120.0 / (M*'+C+'))'),
 ('L(home[0], home[1], 20)','L(home[0], home[1], 30)'),
 ('L(CEN[0], CEN[1], 20)','L(CEN[0], CEN[1], 30)'),
 ('L(CEN[0] + 100.0 / M, CEN[1], 20)','L(CEN[0], CEN[1] + 120.0 / (M*'+C+'), 30)')])
print('MK_OK')
