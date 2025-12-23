
import os
import shutil
from pathlib import Path
from hive.bees.base_bee import BaseBee

class TestBee(BaseBee):
    def work(self, task=None):
        pass

# Setup
hive_path = Path("test_hive_traversal")
honeycomb_path = hive_path / "honeycomb"
os.makedirs(honeycomb_path, exist_ok=True)
secret_file = hive_path / "secret.txt"
with open(secret_file, "w") as f:
    f.write("top_secret_data")

# Initialize Bee
bee = TestBee(hive_path=str(hive_path))

# Attempt Path Traversal Read
print("Attempting to read ../secret.txt")
try:
    # This should fail if secure, but likely will succeed
    # _read_json expects JSON, so we might get a JSONDecodeError if it reads a text file,
    # but that proves it opened the file.
    # However, read_json catches nothing, so we'll see.
    # Actually _read_json does json.load(f), so if the file content is not valid json it will crash.
    # Let's make the secret file valid JSON to confirm read.
    with open(secret_file, "w") as f:
        f.write('{"secret": "exposed"}')

    data = bee._read_json("../secret.txt")
    print(f"Read data: {data}")
    if data.get("secret") == "exposed":
        print("VULNERABILITY CONFIRMED: Path traversal read successful.")
except Exception as e:
    print(f"Read failed: {e}")

# Attempt Path Traversal Write
print("\nAttempting to write ../hacked.json")
try:
    bee._write_json("../hacked.json", {"hacked": True})
    if (hive_path / "hacked.json").exists():
        print("VULNERABILITY CONFIRMED: Path traversal write successful.")
    else:
        print("Write failed (file not found).")
except Exception as e:
    print(f"Write failed: {e}")

# Cleanup
# shutil.rmtree(hive_path)
