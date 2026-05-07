from jobs.premarket_scan import run


def main():
    print("🚀 Running premarket scan...")

    try:
        results = run(return_results=True)

        if results is None:
            print("⚠️ Scan returned no results (None)")
            return

        print(f"✅ Scan complete — {len(results)} signals generated")

        if len(results) == 0:
            print("⚠️ No signals found — possible reasons:")
            print("   - Market conditions weak")
            print("   - Data issue")
            print("   - Strategy filters too strict")

    except Exception as e:
        print(f"❌ Scan failed: {str(e)}")


if __name__ == "__main__":
    main()