#!/usr/bin/env python3
"""Stage B campaign driver (acoustic-resonance gyro attack): seeds x configs, resumable.
usage: python3 campaign_imu.py N_SEEDS [cfg ...]   (run ONLY when the GPS campaign is not running: one SITL at a time)"""
import sys, os, json, subprocess, time
R = __import__("os").environ.get("UAVV_ROOT", "/opt/uavv")
# name: (A rad/s, f Hz)   gyro.x/y += A*sin(2*pi*f*t), t measured from InjectionTimeStart
CFGS = {'gold': None}
for A in (2.0, 8.0, 20.0):
    for f in (10, 50):
        CFGS['AR_A%s_f%d' % (A, f)] = (A, f)
OK = ('disarmed', 'timeout')
n = int(sys.argv[1])
names = sys.argv[2:] or list(CFGS)
log = open(R + '/logs/campaign_imu.log', 'a')
for seed in range(1, n + 1):
    for c in names:
        out = '%s/results/imu/%s/seed%03d' % (R, c, seed)
        try:
            if json.load(open(out + '/meta.json')).get('reason') in OK:
                continue
        except Exception:
            pass
        for attempt in range(3):
            cmd = ['python3', R + '/experiments/runtrial_imu.py', '--seed', str(seed), '--cfg', c]
            if CFGS[c] is None:
                cmd += ['--gold', '--sub', 'AcousticResonance', '--values', '0, 0, 0, 0', '--tstart', '999998', '--tend', '999999']
            else:
                cmd += ['--sub', 'AcousticResonance', '--values', '%s, %s, 0, 0' % CFGS[c], '--tstart', '100', '--tend', '1000']
            t = time.time()
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=R + '/experiments')
            line = (r.stdout.strip().splitlines() or ['?'])[-1]
            log.write('%s seed%d try%d %.0fs %s\n' % (c, seed, attempt, time.time() - t, line)); log.flush()
            try:
                if json.load(open(out + '/meta.json')).get('reason') in OK:
                    break
            except Exception:
                pass
log.write('CAMPAIGN_IMU DONE\n'); log.close()
