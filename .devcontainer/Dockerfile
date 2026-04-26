FROM ros:jazzy-ros-base

# Avoid interactive prompts during apt
ENV DEBIAN_FRONTEND=noninteractive

# Install ROS 2 desktop tools + your stack's dependencies
RUN apt-get update && apt-get install -y \
    ros-jazzy-desktop \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-slam-toolbox \
    ros-jazzy-robot-localization \
    ros-jazzy-urg-node \
    ros-jazzy-teleop-twist-keyboard \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-xacro \
    ros-jazzy-tf2-tools \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    git \
    vim \
    wget \
    xterm \
    && rm -rf /var/lib/apt/lists/*

# Source ROS 2 in every new shell automatically
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc

# Set up workspace
WORKDIR /ros2_ws