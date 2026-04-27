# Start with the ROS 2 Jazzy base image
FROM ros:jazzy-ros-base AS base

# Add build arguments for user selection (use existing ubuntu user)
ARG USER_NAME=ubuntu
ARG USER_UID=1000
ARG USER_GID=1000

# 1. Install dependencies (Root)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    sudo \
    openssh-client \
    curl \
    unzip \
    ca-certificates \
    wget \
    coreutils \
    python3-pip \
    gdb \
    iputils-ping \
    net-tools \
    usbutils \
    build-essential \
    nano \
    yq \
    # Qt/X11 runtime dependencies
    libxcb1 \
    libx11-xcb1 \
    libxcb-glx0 \
    libxcb-xinerama0 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Use existing user/group
# The base image already provides the `ubuntu` user (UID 1000). No need to create users here.

# Setup workspace directory
RUN mkdir -p /home/$USER_NAME/ros2_workspaces/src

# Align fastcdr + typesupport with the current Jazzy snapshot before any
# downstream ROS package builds. Keeps ABIs consistent if Nav2 / slam_toolbox
# pull in upgraded versions later.
RUN . /opt/ros/$ROS_DISTRO/setup.sh && \
    apt-get update && \
    apt-get install -y --only-upgrade \
        ros-$ROS_DISTRO-fastcdr \
        ros-$ROS_DISTRO-rosidl-typesupport-fastrtps-c \
        ros-$ROS_DISTRO-rosidl-typesupport-fastrtps-cpp && \
    rosdep update && \
    rm -rf /var/lib/apt/lists/*

# Fix permissions so the user/group own their workspace
RUN chown -R $USER_UID:$USER_GID /home/$USER_NAME || true

# Configure passwordless sudo for the user
RUN echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" | tee /etc/sudoers.d/$USER_NAME && \
    chmod 0440 /etc/sudoers.d/$USER_NAME

# --- Switch to existing ubuntu user ---
USER $USER_NAME

RUN rosdep update

# Update .bashrc so each shell auto-sources ROS and the workspace overlay
RUN echo "" >> /home/$USER_NAME/.bashrc && \
    echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /home/$USER_NAME/.bashrc && \
    echo "[ -f /home/$USER_NAME/ros2_workspaces/install/setup.bash ] && source /home/$USER_NAME/ros2_workspaces/install/setup.bash" >> /home/$USER_NAME/.bashrc

# ============================================================================
# dev stage — adds Gazebo Harmonic, RViz, and the full sim_bot dependency set
# ============================================================================
FROM base AS dev

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-$ROS_DISTRO-ros-gz \
    ros-$ROS_DISTRO-rviz2 \
    ros-$ROS_DISTRO-gz-ros2-control \
    curl \
    lsb-release \
    gnupg \
    ca-certificates && \
    # Fetch and install OSRF package signing key
    curl -fsSL https://packages.osrfoundation.org/gazebo.gpg -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    # Add Gazebo (OSRF) apt repository for the current distro
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" > /etc/apt/sources.list.d/gazebo-stable.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    gz-harmonic && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# sim_bot stack: SLAM, Nav2, robot_localization (EKF), teleop, xacro tooling, xterm
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-$ROS_DISTRO-slam-toolbox \
    ros-$ROS_DISTRO-navigation2 \
    ros-$ROS_DISTRO-nav2-bringup \
    ros-$ROS_DISTRO-robot-localization \
    ros-$ROS_DISTRO-teleop-twist-keyboard \
    ros-$ROS_DISTRO-teleop-twist-joy \
    ros-$ROS_DISTRO-joint-state-publisher \
    ros-$ROS_DISTRO-joint-state-publisher-gui \
    ros-$ROS_DISTRO-xacro \
    ros-$ROS_DISTRO-tf2-tools \
    ros-$ROS_DISTRO-rqt-graph \
    xterm && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER $USER_NAME
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]

# ============================================================================
# prod stage — minimal runtime, no simulator/GUI
# ============================================================================
FROM base AS prod

USER root

# Headless robot runtime: EKF + Nav2 + slam_toolbox, no Gazebo/RViz.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-$ROS_DISTRO-slam-toolbox \
    ros-$ROS_DISTRO-navigation2 \
    ros-$ROS_DISTRO-nav2-bringup \
    ros-$ROS_DISTRO-robot-localization \
    ros-$ROS_DISTRO-xacro && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER $USER_NAME
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
