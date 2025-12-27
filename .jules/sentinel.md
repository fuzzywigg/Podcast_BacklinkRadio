## 2024-05-23 - Path Traversal in File Operations
**Vulnerability:** Path traversal vulnerability in `BaseBee._read_json` and `BaseBee._write_json` allowed reading and writing files outside the intended `honeycomb` directory using `..` in filenames.
**Learning:** Always validate and sanitize file paths coming from inputs, especially when joining them with a base directory. Relying on `pathlib` joins without checking `is_relative_to` after resolution is insufficient.
**Prevention:** Use `path.resolve()` to get the absolute path and `path.is_relative_to(base_path)` to ensure it stays within the intended sandbox.
