import subprocess
import sys
import time
import os
import signal

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root, "backend")
    frontend_dir = os.path.join(root, "frontend")

    print("===================================================")
    print("Starting graph8 Self-Healing Outbound Agent...")
    print("===================================================")

    # 1. Start Backend
    print("[1/2] Launching FastAPI backend on http://localhost:8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=backend_dir
    )

    time.sleep(2)

    # 2. Start Frontend
    print("[2/2] Launching Vite frontend on http://localhost:5173...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_dir
    )

    print("\nBoth servers are running!")
    print("-> App URL: http://localhost:5173")
    print("-> API Docs: http://localhost:8000/docs")
    print("Press CTRL+C to stop both servers cleanly.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
