# nav2_fault_inject

[![CI](https://github.com/darshmenon/nav2_fault_inject/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/darshmenon/nav2_fault_inject/actions/workflows/ci.yml)
[![ROS 2](https://img.shields.io/badge/ROS%202-Humble%20%7C%20Jazzy-blue)](https://docs.ros.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

Does your robot notice when something dies? Freeze any node of a running ROS 2 stack for a few seconds and watch what happens.

```bash
ros2 run nav2_fault_inject nav2_fault_inject list                       # nodes you can target
ros2 run nav2_fault_inject nav2_fault_inject hang parameter_bridge --for 10   # sim bridge: sensor/TF dropout for 10 s
ros2 run nav2_fault_inject nav2_fault_inject hang controller_server --for 5 # a hung controller
ros2 run nav2_fault_inject nav2_fault_inject run scenario.yaml --timeline out.json
ros2 run nav2_fault_inject nav2_fault_inject --dry-run hang bt_navigator --for 3   # touch nothing
```

```yaml
# scenario.yaml - each node is frozen at `at` seconds for `for` seconds
faults:
  - {at: 20, node: parameter_bridge,  for: 8}
  - {at: 45, node: controller_server, for: 5}
```

## How it works

Pausing the process that hosts a node (`SIGSTOP`, then `SIGCONT`) freezes everything it publishes, with no remaps, no rebuild and no root. Freezing the sim bridge is a sensor and TF dropout; freezing `controller_server` is a hang.

- **Safe by construction.** Only processes in your own `ROS_DOMAIN_ID` whose command line names the node exactly are touched. Every paused process is resumed on exit, on error and on Ctrl+C or `SIGTERM`.
- **Fails before it breaks anything.** A scenario that names a missing node aborts before pausing anything.
- **Reproducible.** Scenarios are timed files, and `--timeline` writes what was paused and resumed, and when.

Pairs with [nav2_doctor](https://github.com/darshmenon/nav2_doctor): break the stack with this, then see the doctor name the cause.

Limits: a node that runs composed inside another process pauses with that whole process, and you can target a node by its name or its executable name (`list` shows both), and only processes started with `--ros-args` are considered. Linux only.

Build: `colcon build --packages-select nav2_fault_inject`. Tests: `python3 -m pytest test` (no ROS needed).
