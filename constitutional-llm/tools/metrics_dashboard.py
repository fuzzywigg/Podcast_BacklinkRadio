import time
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    print(f"Starting Constitutional Metrics Dashboard on port {args.port}...")
    print("Serving compliance metrics from audit logs...")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            # Simulation of a running service
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping dashboard.")

if __name__ == "__main__":
    main()
