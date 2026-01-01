import sys, os, glob, json, math
from pyulog import ULog
import analyze as an
R = an.R

def trial(d):
    meta = json.load(open(d + '/meta.json'))
    out = dict(reason=meta.get('reason'), armed=False)
    try:
        ul = ULog(d + '/flight.ulg', message_name_filter_list=['sensor_gps', 'vehicle_status'])
    except Exception as e:
        out['err'] = str(e)[:60]
        return out
    D = {x.name: x.data for x in ul.data_list}
    vs = D.get('vehicle_status')
    gp = D.get('sensor_gps')
    if vs is None or gp is None:
        return out
    ts = vs['timestamp'] / 1e6
    ar = vs['arming_state']
    idx = [i for i in range(len(ts)) if ar[i] == 2]
    if not idx:
        return out
    t0, t1 = ts[idx[0]], ts[idx[-1]]
    out['armed'] = True
    out['t_flight'] = float(t1 - t0)
    modes = []
    for i in idx:
        s = str(int(vs['nav_state'][i]))
        if not modes or modes[-1] != s:
            modes.append(s)
    out['modes'] = '>'.join(modes)
    gt = gp['timestamp'] / 1e6
    pts = []
    for i in range(len(gt)):
        if t0 <= gt[i] <= t1 + 1 and gp['fix_type'][i] >= 3:
            pts.append((gp['lat'][i] / 1e7, gp['lon'][i] / 1e7, gp['alt'][i] / 1e3))
    if not pts:
        return out
    a0 = pts[0][2]
    P, Q, S = an.xy(*an.HOME), an.xy(*an.CEN), an.xy(*an.N100)
    xt = 0.0
    for p in pts:
        q = an.xy(p[0], p[1])
        xt = max(xt, min(an.seg_dist(q, P, Q), an.seg_dist(q, Q, S)))
    out['xtrack_max'] = xt
    out['alt_max'] = max(p[2] for p in pts) - a0
    e = an.xy(pts[-1][0], pts[-1][1])
    out['end_dist_home'] = math.hypot(e[0] - P[0], e[1] - P[1])
    out['disarmed_in_log'] = bool(ar[-1] != 2)
    out['completed'] = bool(out['disarmed_in_log'] and out['end_dist_home'] < 15.0 and out['alt_max'] > 10)
    return out

def main(kind):
    cfgs = sorted(os.listdir('%s/results/%s' % (R, kind)))
    data = {}
    for c in cfgs:
        data[c] = []
        for d in sorted(glob.glob('%s/results/%s/%s/seed*' % (R, kind, c))):
            if os.path.exists(d + '/flight.ulg') and os.path.exists(d + '/meta.json'):
                t = trial(d)
                t['seed'] = os.path.basename(d)
                data[c].append(t)
    g = data.get('gold', [])
    gx = [t['xtrack_max'] for t in g if 'xtrack_max' in t]
    ge = [t['end_dist_home'] for t in g if 'end_dist_home' in t]
    print('cfg n armed compl[Wilson95] xtrack m/sd/ci | end_dist m/sd | alt_max m | tflight m | p_x p_e')
    rows = []
    for c in cfgs:
        T = data[c]
        fl = [t for t in T if t['armed']]
        k = sum(1 for t in T if t.get('completed'))
        lo, hi = an.wilson(k, len(T))
        r = dict(cfg=c, n=len(T), armed=len(fl), completed=k, lo=lo, hi=hi)
        for key in ('xtrack_max', 'end_dist_home', 'alt_max', 't_flight'):
            v = [t[key] for t in fl if key in t]
            r[key] = an.mean_sd(v) if v else (float('nan'),) * 3
        vx = [t['xtrack_max'] for t in fl if 'xtrack_max' in t]
        ve = [t['end_dist_home'] for t in fl if 'end_dist_home' in t]
        r['px'] = an.perm_p(vx, gx) if c != 'gold' else float('nan')
        r['pe'] = an.perm_p(ve, ge) if c != 'gold' else float('nan')
        rows.append(r)
        xm, ed = r['xtrack_max'], r['end_dist_home']
        print('%s %d %d %d[%.2f-%.2f] %.1f/%.1f/%.1f | %.1f/%.1f | %.1f | %.0f | %.4f %.4f' % (c, r['n'], r['armed'], k, lo, hi,
              xm[0], xm[1], xm[2], ed[0], ed[1], r['alt_max'][0], r['t_flight'][0], r['px'], r['pe']))
    NL = chr(10)
    with open('%s/results/%s_stats.csv' % (R, kind), 'w') as f:
        f.write('cfg,n,armed,completed,comp_lo,comp_hi,xtrack_mean,xtrack_sd,xtrack_ci,end_mean,end_sd,end_ci,alt_mean,tflight_mean,p_xtrack,p_end' + NL)
        for r in rows:
            vals = [r['cfg'], r['n'], r['armed'], r['completed'], r['lo'], r['hi']] + list(r['xtrack_max']) + list(r['end_dist_home']) + [r['alt_max'][0], r['t_flight'][0], r['px'], r['pe']]
            f.write(','.join(str(x) for x in vals) + NL)
    with open('%s/results/%s_trials.csv' % (R, kind), 'w') as f:
        f.write('cfg,seed,reason,armed,completed,xtrack_max,end_dist_home,alt_max,t_flight,modes' + NL)
        for c in cfgs:
            for t in data[c]:
                vals = [c, t['seed'], t['reason'], int(t['armed']), int(bool(t.get('completed'))), t.get('xtrack_max', ''), t.get('end_dist_home', ''), t.get('alt_max', ''), t.get('t_flight', ''), t.get('modes', '')]
                f.write(','.join(str(x) for x in vals) + NL)
    json.dump(data, open('%s/results/%s_trials_ulog.json' % (R, kind), 'w'), indent=1)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'gps')
