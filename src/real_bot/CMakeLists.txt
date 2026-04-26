cmake_minimum_required(VERSION 3.5)
project(real_bot)

if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

install(
  DIRECTORY config description launch maps
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS scripts/waypoint_navigator.py
  PROGRAMS scripts/stepper_odom.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME waypoint_navigator
)

ament_package()
