#!/usr/bin/env bash
# Prepare a SEPARATE copy of the patched PX4 1.13 tree and build it for Gazebo Classic 11
# inside the px4io/px4-dev-simulation-focal container. Your original tree/results are never touched.
set -e
SRC=/opt/uavv
G=$HOME/uavv_gazebo
IMG=px4io/px4-dev-simulation-focal:latest
FCDIR=$SRC/experiments/injections          # absolute path compiled into the injector
mkdir -p "$G/injections" "$G/results" "$G/logs" "$G/experiments"
if [ ! -d "$G/PX4-Autopilot/src" ]; then
  echo "[1/3] copying PX4 tree without build/ ..."
  mkdir -p "$G/PX4-Autopilot"
  tar -C "$SRC/PX4-Autopilot" --exclude=./build -cf - . | tar -C "$G/PX4-Autopilot" -xf -
fi
cp -n "$SRC/experiments/injections/"* "$G/injections/" 2>/dev/null || true
cp -f runtrial_gz.py campaign_gz.py "$G/experiments/"
echo "[2/3] pulling nothing: using local image $IMG"
docker image inspect "$IMG" >/dev/null
echo "[3/3] building PX4 + Gazebo plugins in the container (first time: 10-25 min) ..."
docker run --rm -i --user "$(id -u):$(id -g)" --network host -e HOME=/tmp/home -e HEADLESS=1 \
  -v "$G/PX4-Autopilot:/src" -v "$G/injections:$FCDIR" -w /src "$IMG" \
  bash -c 'mkdir -p /tmp/home && make px4_sitl_default sitl_gazebo' 2>&1 | tee "$G/logs/build.log" | tail -n 25
echo "BUILD STEP FINISHED. Check the last lines above for errors."
