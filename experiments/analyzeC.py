import os, glob, json
import numpy as np
from pyulog import ULog
import analyze as an
R = an.R
G = np.arange(0, 320.0, 1.0)
DS = (20, 60, 100, 200)
import sys ; RC = float(sys.argv[1])
LAGS = range(-60, 61, 5)

def traj(d):
    try:
        ul = ULog(d + '/flight.ulg', message_name_filter_list=['sensor_gps', 'vehicle_status'])
    except Exception:
        return None
    D = {x.name: x.data for x in ul.data_list}
    vs, gp = D.get('vehicle_status'), D.get('sensor_gps')
    if vs is None or gp is None:
        return None
    ts = vs['timestamp'] / 1e6
    idx = np.where(vs['arming_state'] == 2)[0]
    if len(idx) == 0:
        return None
    t0, t1 = ts[idx[0]], ts[idx[-1]]
    gt = gp['timestamp'] / 1e6
    m = (gt >= t0) & (gt <= t1 + 1) & (gp['fix_type'] >= 3)
    if m.sum() < 2:
        return None
    xy = np.array([an.xy(a / 1e7, b / 1e7) for a, b in zip(gp['lat'][m], gp['lon'][m])])
    t = gt[m] - t0
    return np.interp(G, t, xy[:, 0]), np.interp(G, t, xy[:, 1])

def load(c):
    out = []
    for d in sorted(glob.glob('%s/results/gps/%s/seed*' % (R, c))):
        if os.path.exists(d + '/flight.ulg'):
            t = traj(d)
            if t is not None:
                out.append(t)
    return out

gold = load('gold')
RX = np.mean([g[0] for g in gold], axis=0)
RY = np.mean([g[1] for g in gold], axis=0)

def sep(tr, d, lag):
    px = np.interp(G + lag, G, RX) + d
    py = np.interp(G + lag, G, RY)
    return float(min(np.min(np.hypot(tr[0] - px, tr[1] - py)), np.min(np.hypot(tr[0] - px + 2 * d, tr[1] - py))))

cfgs = sorted(os.listdir(R + '/results/gps'))
rows = []
print('cfg n | sep<%dm at lag0 / at any lag in +-60s, per lateral offset d=%s' % (RC, ','.join(str(x) for x in DS)))
for c in cfgs:
    T = load(c)
    cells = []
    for d in DS:
        s0 = [sep(t, d, 0) for t in T]
        sa = [min(sep(t, d, l) for l in LAGS) for t in T]
        k0 = sum(1 for v in s0 if v < RC)
        ka = sum(1 for v in sa if v < RC)
        cells.append('%d/%d' % (k0, ka))
        rows.append((c, len(T), d, k0, ka, float(np.mean(s0)), float(np.mean(sa))))
    print('%s %d | %s' % (c, len(T), ' '.join(cells)))
with open(R + '/results/stageC_conflict.csv', 'w') as f:
    f.write('cfg,n,d_offset_m,conflicts_lag0,conflicts_anylag,mean_minsep_lag0,mean_minsep_anylag' + chr(10))
    for r in rows:
        f.write(','.join(str(x) for x in r) + chr(10))
