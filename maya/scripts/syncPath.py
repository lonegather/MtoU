import os
import sys

ENV_PYTHONPATH = os.getenv('PYTHONPATH').split(os.pathsep)
ENV_PYTHONPATH = list(os.path.realpath(p) for p in ENV_PYTHONPATH)
SYS_PATH = list(os.path.realpath(p) for p in sys.path)

for path in ENV_PYTHONPATH:
    if path not in SYS_PATH:
        sys.path.append(path)
