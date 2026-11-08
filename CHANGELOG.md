# Changelog

## 0.1.2
- Log lines and `--timeline` entries carry wall-clock time (`13:56:07 [  0.01s] PAUSE ...`) so they line up with other tools' logs.

## 0.1.1
- Nodes launched with their default name (no `__node:=`) are now found by executable name, e.g. `controller_server`, `robot_state_publisher`, `parameter_bridge`. Only processes started with `--ros-args` are considered.
- `list` shows the executable name when it differs from the node name.

## 0.1.0
- `list`, `hang` and `run` (timed scenario files) by pausing node processes in your ROS domain.
- Always resumes on exit, error, Ctrl+C or SIGTERM; `--dry-run`; JSON timeline.
