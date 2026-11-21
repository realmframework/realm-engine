## Summary

<!-- Briefly describe what changed and why. -->

## Type of Change

- [ ] Bug fix
- [ ] Security / hardening
- [ ] Feature / enhancement
- [ ] Packaging / cross-platform
- [ ] Documentation / tests

## Verification Checklist

- [ ] `uv run ruff check .` passes with 0 issues
- [ ] `uv run pyright` passes with 0 errors
- [ ] `uv run pyright --pythonplatform Windows` passes with 0 errors
- [ ] `uv run pytest` passes with 0 failures
- [ ] If UI JS changed: `node --check` passed on assembled `CLIENT_SCRIPT`
- [ ] If UI copy changed: EN / DE / ES translations updated with full parity
- [ ] No files exceed architecture line ceilings (`core/test_architecture.py`)
