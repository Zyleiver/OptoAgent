import time
import subprocess
import argparse
import sys
import schedule

def job(query):
    print(f"\n--- Running Scheduled Cycle at {time.ctime()} ---")
    
    # 1. Monitor RSS & Groups
    print("[Scheduler] Running monitor_sources...")
    subprocess.run([sys.executable, "src/main.py", "monitor_sources"])
    
    # 2. Active Search & Idea Generation
    if query:
        print(f"[Scheduler] Running run_cycle for '{query}'...")
        subprocess.run([sys.executable, "src/main.py", "run_cycle", "--query", query, "--limit", "3"])
    
    print("--- Cycle Finished ---\n")

def run_scheduler(interval_hours, query, dry_run=False):
    if dry_run:
        print("Dry Run: Executing job immediately...")
        job(query)
        return

    print(f"Starting Scheduler. Running every {interval_hours} hours. Press Ctrl+C to stop.")
    
    # Schedule the job
    schedule.every(interval_hours).hours.do(job, query=query)
    
    # Run once immediately on start? Optional. Let's run once.
    job(query)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=6, help="Interval in hours")
    parser.add_argument("--query", default="perovskite solar cells", help="Search query for run_cycle")
    parser.add_argument("--dry-run", action="store_true", help="Run once and exit (for testing)")
    args = parser.parse_args()

    run_scheduler(args.interval, args.query, args.dry_run)
