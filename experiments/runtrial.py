#!/usr/bin/env python3
"""One seeded SITL trial: write Fault.fc, boot PX4+jMAVSim (headless), fly a mission through the
injection circle, log MAVLink telemetry (jsonl), keep the ULog, write meta.json. Isolated to uavv-resubmission."""
import os, sys, time, json, signal, subprocess, argparse, glob, shutil
os.environ['MAVLINK20'] = '1'
from pymavlink import mavutil
R = __import__("os").environ.get("UAVV_ROOT", "/opt/uavv")
PX = R + '/PX4-Autopilot'
CEN = (40.212925, -8.4137479)
M = 111320.0
ap = argparse.ArgumentParser()
ap.add_argument('--seed', type=int, default=1)
ap.add_argument('--sub', default='RandomValue')
ap.add_argument('--values', default='394958541, -4069934, 21693, 10, 10, 10')
ap.add_argument('--radius', type=float, default=78)
ap.add_argument('--gold', action='store_true')
ap.add_argument('--cfg', default='test')
ap.add_argument('--timeout', type=int, default=240)
a = ap.parse_args()
out = '%s/results/gps/%s/seed%03d' % (R, a.cfg, a.seed)
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)
loc = (CEN[0] + 1.0, CEN[1]) if a.gold else CEN
fc = ('DroneIP = 127.0.0.1:14540\nMissionPath = /dev/null\nInjectionLocation = [%.8f, %.10f]\n'
      'InjectionRadius = %s\nFaultType = Software\nFaultTarget = GPS\nFaultSubType = %s\nValues = [%s]\n'
      % (loc[0], loc[1], a.radius, a.sub, a.values))
open(R + '/experiments/injections/Fault.fc', 'w').write(fc)
shutil.copy(R + '/experiments/injections/Fault.fc', out + '/Fault.fc')
subprocess.call('pkill -x px4; pkill -f jmavsim_run.jar', shell=True)
time.sleep(2)
rootfs = PX + '/build/px4_sitl_default/tmp/rootfs'
for d in ('eeprom', 'dataman', 'log'):
    shutil.rmtree(rootfs + '/' + d, ignore_errors=True)
home = (CEN[0] - 100.0 / M, CEN[1])
env = dict(os.environ, HEADLESS='1', FI_SEED=str(a.seed), PX4_HOME_LAT='%.7f' % home[0],
           PX4_HOME_LON='%.7f' % home[1], PX4_HOME_ALT='50', CC='gcc-11', CXX='g++-11')
logf = open(out + '/sitl.log', 'w')
proc = subprocess.Popen(['make', 'px4_sitl', 'jmavsim'], cwd=PX, env=env, stdout=logf, stdin=subprocess.PIPE,
                        stderr=subprocess.STDOUT, preexec_fn=os.setsid)
meta = dict(vars(a), home=home, center=CEN, ever_armed=False, reason='?')
rec = open(out + '/telemetry.jsonl', 'w')
t0 = time.time()

def finish():
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        pass
    time.sleep(3)
    subprocess.call('pkill -x px4; pkill -f jmavsim_run.jar', shell=True)
    ul = sorted(glob.glob(rootfs + '/log/*/*.ulg'), key=os.path.getmtime)
    if ul:
        shutil.copy(ul[-1], out + '/flight.ulg')
    meta['t_total'] = time.time() - t0
    json.dump(meta, open(out + '/meta.json', 'w'), indent=1)
    rec.close()
    print('DONE', a.cfg, a.seed, meta['reason'], 'armed' if meta['ever_armed'] else 'never-armed', round(meta['t_total']))
    sys.exit(0)

try:
    m = mavutil.mavlink_connection('udpin:127.0.0.1:14540')
    hb = None
    while time.time() - t0 < 200 and hb is None:
        hb = m.recv_match(type='HEARTBEAT', blocking=True, timeout=2)
    if hb is None:
        meta['reason'] = 'no-heartbeat'
        finish()
    ts, tc = m.target_system, m.target_component
    L = lambda la, lo, z: (int(la * 1e7), int(lo * 1e7), z)
    items = [(22, L(home[0], home[1], 20)), (16, L(CEN[0], CEN[1], 20)),
             (16, L(CEN[0] + 100.0 / M, CEN[1], 20)), (21, L(home[0], home[1], 0))]
    th = time.time()
    while time.time() - th < 120:
        if m.recv_match(type='HOME_POSITION', blocking=True, timeout=1) is not None:
            break
    time.sleep(25)
    meta['t_home'] = round(time.time() - t0, 1)
    ok = False
    meta['upl'] = []
    for attempt in range(3):
        m.mav.mission_clear_all_send(ts, tc)
        m.recv_match(type='MISSION_ACK', blocking=True, timeout=3)
        m.mav.mission_count_send(ts, tc, len(items), 0)
        tu = time.time()
        while time.time() - tu < 25:
            r = m.recv_match(type=['MISSION_REQUEST', 'MISSION_REQUEST_INT', 'MISSION_ACK'], blocking=True, timeout=2)
            if r is None:
                continue
            meta['upl'].append([r.get_type(), getattr(r, 'seq', None), getattr(r, 'type', None)])
            if r.get_type() == 'MISSION_ACK':
                ok = (r.type == 0)
                break
            c, (x, y, z) = items[r.seq]
            if r.get_type() == 'MISSION_REQUEST':
                m.mav.mission_item_send(ts, tc, r.seq, 3, c, 1 if r.seq == 0 else 0, 1, 0, 0, 0, float('nan'), x / 1e7, y / 1e7, z, 0)
            else:
                m.mav.mission_item_int_send(ts, tc, r.seq, 6, c, 1 if r.seq == 0 else 0, 1, 0, 0, 0, float('nan'), x, y, z, 0)
        if ok:
            break
        time.sleep(3)
    meta['mission_ok'] = ok
    if not ok:
        meta['reason'] = 'mission-upload-failed'
        finish()
    armed = False
    t_arm = None
    last = 0
    sent_start = 0
    t_gps = None
    last_mode = 0
    last_hb = 0
    while time.time() - t0 < 400:
        msg = m.recv_match(blocking=True, timeout=0.5)
        now = time.time()
        if now - last_hb > 1:
            m.mav.heartbeat_send(6, 8, 0, 0, 0)
            last_hb = now
        if msg is not None:
            ty = msg.get_type()
            if ty in ('GLOBAL_POSITION_INT', 'GPS_RAW_INT', 'LOCAL_POSITION_NED', 'HEARTBEAT', 'STATUSTEXT', 'MISSION_CURRENT', 'SYS_STATUS', 'ATTITUDE', 'COMMAND_ACK', 'HOME_POSITION'):
                d = msg.to_dict()
                d['_t'] = round(now - t0, 3)
                rec.write(json.dumps(d) + '\n')
                if ty == 'GPS_RAW_INT' and msg.fix_type >= 3 and t_gps is None:
                    t_gps = now
                    meta['t_gps'] = round(now - t0, 1)
                if ty == 'STATUSTEXT':
                    meta.setdefault('statustext', []).append([round(now - t0, 1), d.get('text')])
                if ty == 'HEARTBEAT' and msg.type != 6:
                    was = armed
                    armed = bool(msg.base_mode & 128)
                    meta['last_custom_mode'] = msg.custom_mode
                    amode = (msg.custom_mode >> 16) & 255
                    if amode == 4 and msg.custom_mode // 16777216 in [2, 4, 5]:
                        meta['mission_mode'] = True
                    if armed and not was:
                        t_arm = now
                        meta['ever_armed'] = True
                    if was and not armed:
                        meta['reason'] = 'disarmed'
                        finish()
        if not armed and now - last > 3 and not meta['ever_armed'] and t_gps and now - t_gps > 20:
            m.mav.command_long_send(ts, tc, 400, 0, 1, 0, 0, 0, 0, 0, 0)
            last = now
            meta['n_arm'] = meta.get('n_arm', 0) + 1
        if armed and not meta.get('mission_mode') and now - last_mode > 2:
            m.mav.command_long_send(ts, tc, 176, 0, 1, 4, 4, 0, 0, 0, 0)
            m.mav.command_long_send(ts, tc, 300, 0, 0, 0, 0, 0, 0, 0, 0)
            last_mode = now
            sent_start += 1
        if armed and now - t_arm > a.timeout:
            meta['reason'] = 'timeout'
            finish()
    meta['reason'] = 'global-timeout'
    finish()
except SystemExit:
    raise
except Exception as e:
    meta['reason'] = 'exception: %r' % (e,)
    finish()
