    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[os.path.join(pkg_real_bot, 'config', 'ekf.yaml'),
            {'tf_buffer_duration': 30.0},
        ],
    )