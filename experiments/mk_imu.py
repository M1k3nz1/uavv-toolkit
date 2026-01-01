s = open('runtrial.py').read()
i = s.index("fc = ('DroneIP")
j = s.index('a.values))', i) + len('a.values))')
new = r"""fc = ('DroneIP = 127.0.0.1:14540\nMissionPath = /dev/null\nFaultType = Software\nFaultTarget = gyro\nFaultSubType = %s\nInjectionType = Time\nInjectionTimeStart = %s\nInjectionTimeEnd = %s\nValues = [%s]\n' % (a.sub, a.tstart, a.tend, a.values))"""
s = s[:i] + new + s[j:]
k = s.index("ap.add_argument('--radius'")
e = s.index(chr(10), k)
s = s[:e + 1] + "ap.add_argument('--tstart', default='100')" + chr(10) + "ap.add_argument('--tend', default='1000')" + chr(10) + s[e + 1:]
s = s.replace('results/gps', 'results/imu')
open('runtrial_imu.py', 'w').write(s)
print('ok', s.count('results/imu'), s.count('tstart'))
