#!/usr/bin/env bash
set -Eeuo pipefail

echo "=== 1. Connect ROS 2 and ArduPilot workspaces ==="

source /opt/ros/humble/setup.bash
source "$HOME/ardu_ws/install/setup.bash"

export GZ_VERSION=harmonic

export GZ_SIM_RESOURCE_PATH="$(
    ros2 pkg prefix ardupilot_gazebo
)/share:${HOME}/ardu_ws/src/ardupilot_gazebo/models:${HOME}/ardu_ws/src/ardupilot_gazebo/worlds:${GZ_SIM_RESOURCE_PATH:-}"

export SDF_PATH="$GZ_SIM_RESOURCE_PATH"

cd "$HOME/fpv_labs"

echo "=== 2. Build fpv_lab2 ==="

colcon build --symlink-install --packages-select fpv_lab2

source "$HOME/fpv_labs/install/setup.bash"

echo "=== 3. Start Gazebo maze and ArduPilot SITL ==="

ros2 launch ardupilot_gz_bringup iris_maze.launch.py rviz:=false &
SIM_PID=$!

cleanup() {
    echo "=== Stopping simulation ==="

    if kill -0 "$SIM_PID" 2>/dev/null; then
        kill -INT "$SIM_PID" 2>/dev/null || true
        wait "$SIM_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "=== 4. Wait for ROS 2 interfaces ==="

ready=0

for ((i=0; i<120; i++)); do
    topics="$(ros2 topic list 2>/dev/null || true)"
    services="$(ros2 service list 2>/dev/null || true)"

    if grep -Fxq "/ap/v1/status" <<< "$topics" &&
       grep -Fxq "/odometry" <<< "$topics" &&
       grep -Fxq "/ap/v1/prearm_check" <<< "$services" &&
       grep -Fxq "/ap/v1/mode_switch" <<< "$services" &&
       grep -Fxq "/ap/v1/arm_motors" <<< "$services" &&
       grep -Fxq "/ap/v1/experimental/takeoff" <<< "$services"; then
        ready=1
        break
    fi

    if ! kill -0 "$SIM_PID" 2>/dev/null; then
        echo "Gazebo/ArduPilot launch stopped unexpectedly."
        exit 1
    fi

    sleep 1
done

if [[ "$ready" -ne 1 ]]; then
    echo "Required ROS 2 topics or services were not found."
    ros2 topic list -t || true
    ros2 service list -t || true
    exit 1
fi

echo "=== 5. Verify the drone model ==="

models="$(gz model --list 2>/dev/null || true)"

if ! grep -Eq '^[[:space:]]*-[[:space:]]+iris([[:space:]]|$)' <<< "$models"; then
    echo "Drone model iris was not found in Gazebo."
    printf '%s\n' "$models"
    exit 1
fi

echo "=== 6. Start flight_test ==="

ros2 run fpv_lab2 flight_test
