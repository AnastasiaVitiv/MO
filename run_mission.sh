#!/bin/bash

echo "=== 1. Зупинка попередніх процесів ==="
pkill -9 -f "gz|sitl|ardupilot|micro_ros_agent|rviz2|ros2" 2>/dev/null
sleep 2

echo "=== 2. Експорт змінних та підключення ROS 2 ==="
export DISPLAY=:0
export GZ_VERSION=harmonic
export LIBGL_ALWAYS_SOFTWARE=1
export GZ_SIM_RESOURCE_PATH=$HOME/ardu_ws/src:$HOME/ardu_ws/src/ardupilot_gazebo/models:$HOME/ardu_ws/src/ardupilot_gazebo/worlds:$GZ_SIM_RESOURCE_PATH
export SDF_PATH=$HOME/ardu_ws/src/ardupilot_gazebo/models:$SDF_PATH

source /opt/ros/humble/setup.bash
source ~/ardu_ws/install/setup.bash
source ~/fpv_labs/install/setup.bash

echo "=== 3. Запуск симуляції Gazebo + ArduPilot SITL ==="
ros2 launch ardupilot_gz_bringup iris_runway.launch.py rviz:=false &

echo "=== 4. Очікування повної ініціалізації ArduPilot ==="
sleep 50
echo "=== 5. Запуск автономної місії ==="
ros2 run fpv_lab2 flight_test
