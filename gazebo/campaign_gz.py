#!/usr/bin/env python3
"""Gazebo replication campaign: seeds x configs, resumable, retries infrastructure failures.
usage: python3 campaign_gz.py N_SEEDS cfg1 cfg2 ...   (default configs = the replication set below)"""
import sys, os, json, subprocess, time
G = os.path.expanduser('~/uavv_gazebo')
CFGS = {   # identical fault definitions to the jMAVSim campaign (campaign.py)
    'gold': (None, None),
    'MaxAltitude': ('MaxAltitude', '0, 0, 0, 0'),
    'FixedNoise': ('FixedNoise', '5000, 5000, 0, 0'),
    'ZigZag': ('ZigZag', '3000, 3000, 0, 0'),
    'FixedValue': ('FixedValue', '402200000, -84137479, 70000, 0'),
    'FreezeValue': ('FreezeValue', '0, 0, 0, 0'),
}
OK = ('disarmed', 'timeout')
n = int(sys.argv[1])
names = sys.argv[2:] or list(CFGS)
os.makedirs(G + '/logs', exist_ok=True)
log = open(G + '/logs/campaign_gz.log', 'a')
for seed in range(1, n + 1):
    for c in names:
        out = '%s/results/gps/%s/seed%03d' % (G, c, seed)
        try:
            if json.load(open(out + '/meta.json')).get('reason') in OK:
                continue
        except Exception:
            pass
        sub, vals = CFGS[c]
        for attempt in range(3):
            cmd = ['python3', G + '/experiments/runtrial_gz.py', '--seed', str(seed), '--cfg', c]
            cmd += ['--gold'] if sub is None else ['--sub', sub, '--values', vals]
            t = time.time()
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=G + '/experiments')
            line = (r.stdout.strip().splitlines() or ['?'])[-1]
            log.write('%s seed%d try%d %.0fs %s\n' % (c, seed, attempt, time.time() - t, line)); log.flush()
            try:
                if json.load(open(out + '/meta.json')).get('reason') in OK:
                    break
            except Exception:
                pass
log.write('CAMPAIGN DONE\n'); log.close()
