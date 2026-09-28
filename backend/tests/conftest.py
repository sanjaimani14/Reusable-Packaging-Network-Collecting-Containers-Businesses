import os
import sys

# Ensure root, repackai, and backend are on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, ".."))
repackai_dir = os.path.abspath(os.path.join(backend_dir, ".."))
root_dir = os.path.abspath(os.path.join(repackai_dir, ".."))

for path in [root_dir, repackai_dir, backend_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)
