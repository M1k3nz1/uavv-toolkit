#!/usr/bin/env python3
"""Stage A analysis: per-trial metrics from telemetry.jsonl + meta.json, then per-config statistics
(mean, SD, 95% t-CI, Wilson CI for proportions, permutation test vs gold). Stdlib only."""
import sys, os, json, glob, math, random
R = __import__("os").environ.get("UAVV_ROOT", "/opt/uavv")
CEN = (40.212925, -8.4137479)
M = 111320.0
HOME = (CEN[0] - 100.0 / M, CEN[1])
N100 = (CEN[0] + 100.0 / M, CEN[1])
KX = M * math.cos(math.radians(CEN[0]))
TCRIT = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23, 12: 2.18, 15: 2.13,
         20: 2.09, 25: 2.06, 30: 2.04, 40: 2.02, 60: 2.0}

def tcrit(df):
    k = max(x for x in TCRIT if x <= max(df, 1))
    return TCRIT[k] if df < 60 else 1.96

def xy(lat, lon):
    return ((lon - CEN[1]) * KX, (lat - CEN[0]) * M)

def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)

def trial(d):
    meta = json.load(open(d + '/meta.json'))
    gp, hb = [], []
    for l in open(d + '/telemetry.jsonl'):
        r = json.loads(l)
        t = r['mavpackettype']
        if t == 'GLOBAL_POSITION_INT':
            gp.append((r['_t'], r['lat'] / 1e7, r['lon'] / 1e7, r['relative_alt'] / 1e3))
        elif t == 'HEARTBEAT' and r['type'] != 6:
            hb.append((r['_t'], bool(r['base_mode'] & 128), (r['custom_mode'] >> 16) & 255, r['custom_mode'] >> 24))
    arm = [h for h in hb if h[1]]
    out = dict(reason=meta.get('reason'), armed=bool(arm))
    if not arm:
        return out
    t0, t1 = arm[0][0], arm[-1][0]
    out['t_flight'] = t1 - t0
    modes = []
    for h in arm:
        s = '%d.%d' % (h[2], h[3])
        if not modes or modes[-1] != s:
            modes.append(s)
    out['modes'] = '>'.join(modes)
    fl = [g for g in gp if t0 <= g[0] <= t1]
    if fl:
        A, B, C = xy(*HOME), xy(*CEN), xy(*N100)
        out['xtrack_max'] = max(min(seg_dist(xy(g[1], g[2]), A, B), seg_dist(xy(g[1], g[2]), B, C)) for g in fl)
        out['alt_max'] = max(g[3] for g in fl)
        e = xy(fl[-1][1], fl[-1][2])
        out['end_dist_home'] = math.hypot(e[0] - A[0], e[1] - A[1])
    out['completed'] = (meta.get('reason') == 'disarmed' and out.get('end_dist_home', 1e9) < 15.0 and out.get('alt_max', 0) > 10.0)
    return out

def mean_sd(v):
    n = len(v); m = sum(v) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1)) if n > 1 else 0.0
    ci = tcrit(n - 1) * sd / math.sqrt(n) if n > 1 else float('nan')
    return m, sd, ci

def wilson(k, n, z=1.96):
    if n == 0:
        return (float('nan'),) * 2
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h

def perm_p(a, b, it=10000):
    if len(a) < 2 or len(b) < 2:
        return float('nan')
    rnd = random.Random(1)
    obs = abs(sum(a) / len(a) - sum(b) / len(b)); pool = a + b; k = 0
    for _ in range(it):
        rnd.shuffle(pool)
        if abs(sum(pool[:len(a)]) / len(a) - sum(pool[len(a):]) / len(b)) >= obs - 1e-12:
            k += 1
    return (k + 1) / (it + 1)

def main():
    cfgs = sorted(os.listdir(R + '/results/gps'))
    data = {}
    for c in cfgs:
        data[c] = []
        for d in sorted(glob.glob('%s/results/gps/%s/seed*' % (R, c))):
            if os.path.exists(d + '/meta.json') and os.path.exists(d + '/telemetry.jsonl'):
                data[c].append(trial(d))
    rows = []
    for c in cfgs:
        T = data[c]
        n = len(T)
        fl = [t for t in T if t['armed']]
        k = sum(1 for t in T if t.get('completed'))
        lo, hi = wilson(k, n)
        row = dict(cfg=c, n=n, armed=len(fl), completed=k, comp_lo=lo, comp_hi=hi)
        for key in ('xtrack_max', 'end_dist_home', 't_flight', 'alt_max'):
            v = [t[key] for t in fl if key in t]
            if v:
                row[key] = mean_sd(v)
        rows.append(row)
    g = [t['xtrack_max'] for t in data.get('gold', []) if 'xtrack_max' in t]
    print('cfg n armed compl[95%Wilson] xtrack_max m/sd/ci  end_dist m/sd  tflight m  p_vs_gold(xtrack)')
    for r in rows:
        x = r.get('xtrack_max', (float('nan'),) * 3); e = r.get('end_dist_home', (float('nan'),) * 3); f = r.get('t_flight', (float('nan'),) * 3)
        v = [t['xtrack_max'] for t in data[r['cfg']] if 'xtrack_max' in t]
        p = perm_p(v, g) if r['cfg'] != 'gold' else float('nan')
        print('%s %d %d %d[%.2f-%.2f] %.1f/%.1f/%.1f %.1f/%.1f %.0f p=%.4f' % (r['cfg'], r['n'], r['armed'], r['completed'],
              r['comp_lo'], r['comp_hi'], x[0], x[1], x[2], e[0], e[1], f[0], p))
    with open(R + '/results/gps_summary.csv', 'w') as f:
        f.write('cfg,seed_idx,reason,armed,completed,xtrack_max,end_dist_home,t_flight,alt_max,modes\n')
        for c in cfgs:
            for i, t in enumerate(data[c]):
                f.write('%s,%d,%s,%d,%d,%s,%s,%s,%s,%s\n' % (c, i, t['reason'], t['armed'], int(bool(t.get('completed'))),
                        t.get('xtrack_max', ''), t.get('end_dist_home', ''), t.get('t_flight', ''), t.get('alt_max', ''), t.get('modes', '')))
    json.dump(data, open(R + '/results/gps_trials.json', 'w'), indent=1)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        print(json.dumps(trial(sys.argv[1]), indent=1))
    else:
        main()
