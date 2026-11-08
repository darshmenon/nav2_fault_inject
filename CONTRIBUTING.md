# Contributing

- Fault logic lives in `nav2_fault_inject/faults.py`; test it against a fake `/proc` tree or a real throw-away process, no ROS needed.
- Run `python3 -m pytest -q test` before opening a PR.
- Bump the version in `__init__.py`, `package.xml` and `setup.py` together and add a `CHANGELOG.md` entry.
- Keep commit messages short, one line.
