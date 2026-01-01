# Deployment

## Harness and patched PX4 (what the paper's evaluation used)
- Linux (tested on Ubuntu), Python 3 with `pymavlink`, `numpy`, `scipy`; PX4 build dependencies; Java for jMAVSim.
- Build the patched PX4 SITL (`make px4_sitl jmavsim`). The patched publishers read the fault file from the path compiled in the patch
  (`/opt/uavv/injections/Fault.fc`) and write logs under `/opt/uavv/logs/faultlog`:
  `sudo mkdir -p /opt/uavv/{results,logs/faultlog,injections} && sudo chown -R $USER /opt/uavv`.
- The harness expects `/opt/uavv/PX4-Autopilot` (patched tree), `/opt/uavv/experiments` and `/opt/uavv/injections`; the root can be
  changed with `UAVV_ROOT`. The seed is passed through the environment variable `FI_SEED`.
- MAVLink connection: UDP `127.0.0.1:14540`; one trial ends after 240 s or at disarm.

## Gazebo replication
- Needs Docker. `gazebo/gz_setup.sh` pulls `px4io/px4-dev-simulation-focal` (Ubuntu 20.04, Gazebo Classic 11) and builds the patched tree in a
  copy mounted at `/src`; `campaign_gz.py` then runs each trial in a container (`--network host`).

## Java campaign controller (full toolkit)
- JDK 11+ with JavaFX, plus the libraries used by the sources (JSch for SFTP). Open `toolkit/java-controller` in an IDE, add the libraries,
  run `userInterface.Main`. The controller builds fault files from a campaign CSV (see `toolkit/campaign-examples`), copies them and the
  mission plans to the target machine, starts PX4 with Gazebo (`Tools/gazebo_sitl_multiple_run.sh`) and the DroneKit script.
- Target machines are configured in the UI (`Machine`: address, user, password, injection/mission/autopilot directories).
