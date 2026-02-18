import time
import subprocess
import argparse
import sys

def run_scheduler(interval_hours, query, webhook):
    print(f"Starting Scheduler. Running every {interval_hours} hours.")
    while True:
        print(f"\n--- Running Cycle at {time.ctime()} ---")
        cmd = [sys.executable, "src/main.py", "run_cycle", "--query", query]
        if webhook:
            cmd.extend(["--webhook", webhook])
        
        subprocess.run(cmd)
        
        print(f"Cycle finished. Sleeping for {interval_hours} hours...")
        time.sleep(interval_hours * 3600)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=24, help="Interval in hours")
    parser.add_argument("--query", default="perovskite solar cells", help="Search query")
    parser.add_argument("--webhook", help="Feishu Webhook URL")
    args = parser.parse_args()

    run_scheduler(args.interval, args.query, args.webhook)
