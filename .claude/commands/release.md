# Release a new version to PyPI

Release a new version of rav to PyPI via GitHub Actions.

## Arguments (optional)

- `$ARGUMENTS` - Bump type: `patch` (default), `minor`, or `major`. Or a specific version like `0.5.0`.

## Steps

1. Read the current version from `rav/__init__.py`
2. Determine the new version:
   - If no argument or `patch`: increment patch (0.4.1 -> 0.4.2)
   - If `minor`: increment minor, reset patch (0.4.1 -> 0.5.0)
   - If `major`: increment major, reset minor and patch (0.4.1 -> 1.0.0)
   - If specific version provided: use that version
3. Update the version in `pyproject.toml` (the `version` field)
4. Update the version in `rav/__init__.py` (the `__version__` variable)
5. Run `uv lock` to update the lock file
6. Commit the changes with message: `Bump version to v{version}`
7. Create a git tag: `v{version}`
8. Push the commit and tag to origin

## Important

- Do NOT include a co-authored-by line in commits
- The version should be in format `X.Y.Z` (e.g., `0.4.2`)
