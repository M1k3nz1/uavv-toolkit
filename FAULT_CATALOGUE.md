# Fault catalogue

Fault sub-types recognised by the patched PX4 sensor publishers. This list is generated from the patched source files, so it
matches the code in `patch/px4-1.13-uavv.patch`. A fault is selected in `Fault.fc` with `FaultTarget` and `FaultSubType`, a
time window (`InjectionTimeStart`, `InjectionTimeEnd`, seconds after arming) and a `Values` vector (see `injections/` for examples).

## GPS (VehicleGPSPosition.cpp)

- `DelayValue`
- `FixedNoise`
- `FixedValue`
- `ForceLanding`
- `FreezeAlt`
- `FreezeLat`
- `FreezeLon`
- `FreezeValue`
- `HijackByFixedPosition`
- `HijackByUAV`
- `MaxAltitude`
- `MaxLatitude`
- `MaxLongtitude`
- `MinAltitude`
- `MinLatitude`
- `MinLongtitude`
- `NoUpdates`
- `RandomLatitude`
- `RandomLongtitude`
- `RandomNoise`
- `RandomValue`
- `VeryHighAlt`
- `ZigZag`

## IMU (VehicleIMU.cpp)

- `AcousticResonance`
- `FixedValue`
- `FreezeValue`
- `MaxValue`
- `MinValue`
- `RandomNoise`
- `RandomValue`

Notes: (1) the list contains every sub-type name the code recognises; not all of them are evaluated in the paper, and some are kept from an earlier prototype.
(2) Matching uses `std::string::find` on the sub-type string, so a name that contains another recognised name also selects that branch; the IMU publisher additionally uses the short internal tags `SF` and `A` inside its branches, which are not stand-alone fault names.

User-defined faults are Python functions in the DroneKit scripts (see `toolkit/campaign-runners`).
