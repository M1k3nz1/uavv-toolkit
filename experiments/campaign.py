#!/usr/bin/env python3
"""Stage A campaign driver: seeds x configs, resumable (skips finished trials), retries infrastructure failures.
usage: python3 campaign.py N_SEEDS cfg1 cfg2 ...   (cfg names are keys of CFGS; 'gold' = no fault)"""
import sys, os, json, subprocess, time
R = __import__("os").environ.get("UAVV_ROOT", "/opt/uavv")
# name: (FaultSubType, Values)   -- filled after enumerating subtypes in VehicleGPSPosition.cpp
CFGS = {
    'gold': (None, None),
    'RandomValue': ('RandomValue', '0, 0, 0, 0'),
    'RandomNoise': ('RandomNoise', '0, 0, 0, 0'),
    'FixedValue': ('FixedValue', '402200000, -84137479, 70000, 0'),
    'FixedNoise': ('FixedNoise', '5000, 5000, 0, 0'),
    'ZigZag': ('ZigZag', '3000, 3000, 0, 0'),
    'FreezeValue': ('FreezeValue', '0, 0, 0, 0'),
    'MaxAltitude': ('MaxAltitude', '0, 0, 0, 0'),
    'MinLatitude': ('MinLatitude', '0, 0, 0, 0'),
    'DelayValue': ('DelayValue', '1, 0, 0, 0'),
}
OK = ('disarmed', 'timeout')
n = int(sys.argv[1])
names = sys.argv[2:] or list(CFGS)
log = open(R + '/logs/campaign.log', 'a')
for seed in range(1, n + 1):
    for c in names:
        out = '%s/results/gps/%s/seed%03d' % (R, c, seed)
        try:
            if json.load(open(out + '/meta.json')).get('reason') in OK:
                continue
        except Exception:
            pass
        sub, vals = CFGS[c]
        for attempt in range(3):
            cmd = ['python3', R + '/experiments/runtrial.py', '--seed', str(seed), '--cfg', c]
            cmd += ['--gold'] if sub is None else ['--sub', sub, '--values', vals]
            t = time.time()
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=R + '/experiments')
            line = (r.stdout.strip().splitlines() or ['?'])[-1]
            log.write('%s seed%d try%d %.0fs %s\n' % (c, seed, attempt, time.time() - t, line)); log.flush()
            try:
                if json.load(open(out + '/meta.json')).get('reason') in OK:
                    break
            except Exception:
                pass
log.write('CAMPAIGN DONE\n'); log.close()
