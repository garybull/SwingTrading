from jobs.premarket_scan import run

if __name__ == "__main__":
    print("🚀 Running scan...")
    run(return_results=False)
    print("✅ Scan complete")