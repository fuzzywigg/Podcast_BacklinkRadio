## Sentinel's Journal

## 2024-05-22 - Path Traversal in BaseBee
**Vulnerability:** `BaseBee` allowed reading and writing files outside of the `honeycomb` directory using `..` in filenames.
**Learning:** Even internal helper methods like `_read_json` need to validate inputs if they are ever used with data that might be influenced by a bee's logic (which could be compromised or buggy).
**Prevention:** Use `pathlib.Path.resolve()` to canonicalize paths and check if they start with the expected parent directory.
