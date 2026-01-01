p = '../PX4-Autopilot/src/modules/sensors/vehicle_imu/VehicleIMU.cpp'
L = open(p).read().split(chr(10))
if any('AcousticResonance' in l for l in L):
    print('already patched')
    raise SystemExit
g = next(i for i, l in enumerate(L) if 'FaultTarget_IMU.find("gyro")' in l)
r = next(i for i in range(g, len(L)) if 'FaultSubType_IMU.find("RandomNoise")' in L[i])
new = ['}else if(FaultSubType_IMU.find("AcousticResonance") != std::string::npos){',
 ' static bool ar_logged = false;',
 ' float ar_t = (float)((gyro.timestamp - InjectionTimeStart_IMU) * 1e-6);',
 ' float ar_s = (float)DoubleValues_IMU[0] * sinf(2.0f * 3.14159265f * (float)DoubleValues_IMU[1] * ar_t);',
 ' if (!ar_logged) { PX4_INFO("AcousticResonance A=%.3f f=%.1f", (double)DoubleValues_IMU[0], (double)DoubleValues_IMU[1]); ar_logged = true; }',
 ' gyro.x += ar_s; gyro.y += ar_s;']
L[r:r] = new
open(p, 'w').write(chr(10).join(L))
print('patched', g + 1, r + 1)
