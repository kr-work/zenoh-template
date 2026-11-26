# ROS 2 の最小構成(ros-core)に、2 種類の RMW と demo_nodes_cpp を入れたイメージ。
#   - rmw_cyclonedds_cpp : zenoh-bridge-ros2dds と組み合わせる DDS 実装(ブリッジはこれで試験されている)
#   - rmw_zenoh_cpp      : ROS 2 の通信そのものを Zenoh で行う RMW
ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-core

ARG ROS_DISTRO
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
        ros-${ROS_DISTRO}-rmw-zenoh-cpp \
        ros-${ROS_DISTRO}-demo-nodes-cpp \
    && rm -rf /var/lib/apt/lists/*
