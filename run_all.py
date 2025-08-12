import subprocess, sys, os, signal, time

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

# Environment for orchestrator to find models
env = os.environ.copy()
env.setdefault("MODEL_A_URL", "http://127.0.0.1:8001/predict")
env.setdefault("MODEL_B_URL", "http://127.0.0.1:8002/predict")

processes = []

def spawn(cmd, name):
    print(f"[RUN] {name}: {' '.join(cmd)}")
    return subprocess.Popen(cmd, env=env)

def main():
    try:
        procs = [
            spawn([sys.executable, "-m", "uvicorn", "model_a.app.main:app", "--host", "127.0.0.1", "--port", "8001"], "model_a"),
            spawn([sys.executable, "-m", "uvicorn", "model_b.app.main:app", "--host", "127.0.0.1", "--port", "8002"], "model_b"),
        ]
        #models start
        time.sleep(0.8)
        procs.append(
            spawn([sys.executable, "-m", "uvicorn", "orchestrator.app.main:app", "--host", "127.0.0.1", "--port", "8000"], "orchestrator")
        )

        global processes
        processes = procs

        print("\nAll services starting...")
        print("Orchestrator: http://127.0.0.1:8000")
        print("Model A:      http://127.0.0.1:8001")
        print("Model B:      http://127.0.0.1:8002")
        print("\nPress Ctrl+C to stop.\n")

        # Wait
        procs[-1].wait()
    except KeyboardInterrupt:
        pass
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
        # time
        time.sleep(0.5)
        for p in processes:
            if p.poll() is None:
                p.kill()

if __name__ == "__main__":
    main()