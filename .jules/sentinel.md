## 2025-12-25 - Path Traversal Vulnerability in BaseBee
**Vulnerability:** Found that `_read_json` and `_write_json` in `BaseBee` accepted arbitrary paths, allowing access to files outside the intended directory via `../` traversal.
**Learning:** Even internal helper methods should validate paths when dealing with user or variable input. Assumptions about relative paths can be dangerous.
**Prevention:** Use `pathlib.Path.resolve()` and `is_relative_to()` (Python 3.9+) to strictly enforce directory boundaries.
## Sentinel's Journal

## 2024-05-22 - Path Traversal in BaseBee
**Vulnerability:** `BaseBee` allowed reading and writing files outside of the `honeycomb` directory using `..` in filenames.
**Learning:** Even internal helper methods like `_read_json` need to validate inputs if they are ever used with data that might be influenced by a bee's logic (which could be compromised or buggy).
**Prevention:** Use `pathlib.Path.resolve()` to canonicalize paths and check if they start with the expected parent directory.
