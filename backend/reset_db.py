"""Helper wrapper to run reset_database from backend directory."""
import os
import subprocess
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
script = os.path.join(root, "reset_database.py")
sys.exit(subprocess.call([sys.executable, script]))
