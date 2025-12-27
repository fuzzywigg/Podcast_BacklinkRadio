## 2025-12-25 - Path Traversal Vulnerability in BaseBee
**Vulnerability:** Found that `_read_json` and `_write_json` in `BaseBee` accepted arbitrary paths, allowing access to files outside the intended directory via `../` traversal.
**Learning:** Even internal helper methods should validate paths when dealing with user or variable input. Assumptions about relative paths can be dangerous.
**Prevention:** Use `pathlib.Path.resolve()` and `is_relative_to()` (Python 3.9+) to strictly enforce directory boundaries.
