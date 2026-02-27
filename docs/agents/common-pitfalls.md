# Common Pitfalls

This document records frequently encountered issues and their solutions.

## Build and Development Issues

### Issue: Running Full Test Suite When Only One Group is Needed

**Problem**: `make test` runs all three groups (unit, integration, private) + combines coverage — slower than necessary when validating a single area

**Solution**: Use individual targets for faster feedback:
```bash
make test-unit
make test-integration
make test-private
```

**Note**: Always run `make test` (full suite) when you need the combined coverage report or final validation before committing.

### Issue: Forgetting That Format Runs in Multiple Passes

**Problem**: Running `ruff format` manually once may leave code that needs re-formatting after `add-trailing-comma` runs

**Solution**: Always use `make format` — it handles the full sequence (docformatter → ruff format → ruff check fix → add-trailing-comma → ruff format again → ruff check fix again). Don't run individual formatting tools in isolation.

### Issue: Lint Failing After Manual Edits

**Problem**: Manually editing files and then running `make lint` fails because formatting is off

**Solution**: Always run `make format` before `make lint`. The lint step is read-only (uses `--diff`) and will fail if formatting isn't already applied.

## Code Quality Issues

### Issue: Not Activating Virtual Environment

**Problem**: Running commands without activating venv leads to wrong tool versions or missing dependencies

**Solution**: `source .venv/bin/activate`

**Check**: Verify with `which python` — should point to `.venv/bin/python`

### Issue: Private Method Access Outside tests/private/

**Problem**: The linter allows private member access only in `tests/private/`. Accessing private methods in `tests/unit/` or `tests/integration/` will cause a lint failure.

**Solution**: If you must test a private method directly, put it in `tests/private/`. Prefer testing private behavior through the public interface in `tests/unit/` instead.

## Agent Workflow Issues

### Issue: Not Updating Agent Notes When User Provides Guidance

**Problem**: Agent reads `docs/agents/` notes at the start of a session but doesn't update them when the user provides important guidance during the work

**Context**: The agent learning system in `docs/agents/` is designed to build institutional knowledge across sessions. If agents don't update notes when they learn something, future sessions will repeat the same mistakes.

**What Should Happen**: When the user provides guidance that changes your approach (especially corrections):
1. **Immediately** update the relevant file in `docs/agents/`
2. Don't wait to be asked
3. This ensures future sessions benefit from the learning

**Guideline**: Treat user corrections as high-value learning opportunities. Update the agent notes system immediately when you receive them.

## Notes to Add

- Common HTML linting rule edge cases
- Common test failures and their fixes
- mypy type error patterns
