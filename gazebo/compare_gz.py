#!/usr/bin/env python3
"""Compare the Gazebo replication with the jMAVSim campaign, using the SAME scoring code (analyze.py).
usage: python3 compare_gz.py            (paths default to the VM layout; override with --jm/--gz)
Writes: results/compare_gz_trials.csv, results/compare_gz.txt, results/compare_gz.tex under the Gazebo folder."""
import sys, os, json, glob, math, argparse, importlib.util
ap = argparse.ArgumentParser()
ap.add_argument('--jm', default=os.path.expanduser('/opt/uavv'))
ap.add_argument('--gz', default=os.path.expanduser('~/uavv_gazebo'))
a = ap.parse_args()
spec = importlib.util.spec_from_file_location('an', a.jm + '/experiments/analyze.py')
an = importlib.util.module_from_spec(spec); spec.loader.exec_module(an)
CFGS = ['gold', 'MaxAltitude', 'FixedNoise', 'ZigZag', 'FixedValue', 'FreezeValue']
OK = ('disarmed', 'timeout')

def load(root, c, first=None):
    T, bad = [], 0
    for d in sorted(glob.glob('%s/results/gps/%s/seed*' % (root, c))):
        if not (os.path.exists(d + '/meta.json') and os.path.exists(d + '/telemetry.jsonl')):
            continue
        if first and int(d[-3:]) > first:
            continue
        t = an.trial(d); t['seed'] = int(d[-3:])
        if t['reason'] not in OK:
            bad += 1
        T.append(t)
    return T, bad

def summ(T):
    fl = [t for t in T if t['armed']]
    n = len(T); k = sum(1 for t in T if t.get('completed'))
    s = dict(n=n, k=k, w=an.wilson(k, n) if n else (float('nan'),) * 2)
    for key in ('xtrack_max', 'end_dist_home', 't_flight'):
        v = [t[key] for t in fl if key in t]
        s[key] = an.mean_sd(v) if v else (float('nan'),) * 3
    return s

def klass(s):
    if s['n'] == 0: return '-'
    r = s['k'] / s['n']
    if r >= 0.8: return 'no effect' if s['xtrack_max'][0] < 5 else 'displaced'
    if r <= 0.2: return 'failed'
    return 'mixed'

def vals(T, key):
    return [t[key] for t in T if key in t]

out, rows, csv = [], [], ['simulator,cfg,seed,reason,armed,completed,xtrack_max,end_dist_home,t_flight,alt_max,modes']
out.append('Simulator comparison, same scoring code (completed = disarmed, ended within 15 m of start, climbed above 10 m)')
out.append('%-12s %-9s %2s %-20s %-16s %-14s %5s  %s' % ('config', 'sim', 'n', 'completed[Wilson95]', 'xtrack m (sd)', 'end dist m', 't s', 'class'))
infra = []
for c in CFGS:
    J, bj = load(a.jm, c); Jf, _ = load(a.jm, c, first=5); G, bg = load(a.gz, c)
    if bg or bj: infra.append((c, bj, bg))
    for name, T in (('jMAVSim', J), ('jMAV-s1-5', Jf), ('Gazebo', G)):
        s = summ(T)
        out.append('%-12s %-9s %2d %2d [%.2f-%.2f]      %5.1f (%4.1f)     %5.1f (%4.1f)  %5.0f  %s' % (
            c, name, s['n'], s['k'], s['w'][0], s['w'][1], s['xtrack_max'][0], s['xtrack_max'][1],
            s['end_dist_home'][0], s['end_dist_home'][1], s['t_flight'][0], klass(s) if c != 'gold' else 'baseline'))
        rows.append((c, name, s, T))
        for t in T:
            csv.append('%s,%s,%d,%s,%d,%d,%s,%s,%s,%s,%s' % (name, c, t['seed'], t['reason'], t['armed'], int(bool(t.get('completed'))),
                       t.get('xtrack_max', ''), t.get('end_dist_home', ''), t.get('t_flight', ''), t.get('alt_max', ''), t.get('modes', '')))
    out.append('')
out.append('Agreement per fault (permutation test on cross-track and end distance, jMAVSim all seeds vs Gazebo; p never 0)')
out.append('%-12s %-10s %-10s %-6s %-10s %-10s' % ('config', 'jMAVSim', 'Gazebo', 'same?', 'p_xtrack', 'p_enddist'))
tex = ['\\begin{tabular}{lcccc}', '\\toprule',
       'Fault & \\multicolumn{2}{c}{Completed} & \\multicolumn{2}{c}{Cross-track (m)} \\\\',
       ' & jMAVSim & Gazebo & jMAVSim & Gazebo \\\\', '\\midrule']
same_all = True
for c in CFGS:
    sj = [r for r in rows if r[0] == c and r[1] == 'jMAVSim'][0]; sg = [r for r in rows if r[0] == c and r[1] == 'Gazebo'][0]
    kj, kg = klass(sj[2]), klass(sg[2])
    px = an.perm_p(vals(sj[3], 'xtrack_max'), vals(sg[3], 'xtrack_max'))
    pe = an.perm_p(vals(sj[3], 'end_dist_home'), vals(sg[3], 'end_dist_home'))
    same = (c == 'gold') or kj == kg
    same_all = same_all and same
    out.append('%-12s %-10s %-10s %-6s %-10.4f %-10.4f' % (c, kj if c != 'gold' else '-', kg if c != 'gold' else '-', 'yes' if same else 'NO', px, pe))
    tex.append('%s & %d/%d & %d/%d & %.1f$\\pm$%.1f & %.1f$\\pm$%.1f \\\\' % (c, sj[2]['k'], sj[2]['n'], sg[2]['k'], sg[2]['n'],
               sj[2]['xtrack_max'][0], sj[2]['xtrack_max'][1], sg[2]['xtrack_max'][0], sg[2]['xtrack_max'][1]))
tex += ['\\bottomrule', '\\end{tabular}']
out.append('')
out.append('Outcome class identical for every fault: %s' % ('YES' if same_all else 'NO - see rows marked NO'))
if infra:
    out.append('WARNING: trials that ended for an infrastructure reason (not disarmed/timeout): ' + ', '.join('%s jM=%d gz=%d' % x for x in infra))
os.makedirs(a.gz + '/results', exist_ok=True)
open(a.gz + '/results/compare_gz.txt', 'w').write('\n'.join(out) + '\n')
open(a.gz + '/results/compare_gz.tex', 'w').write('\n'.join(tex) + '\n')
open(a.gz + '/results/compare_gz_trials.csv', 'w').write('\n'.join(csv) + '\n')
print('\n'.join(out))
print('\nwritten: compare_gz.txt, compare_gz.tex, compare_gz_trials.csv in', a.gz + '/results')
