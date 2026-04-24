## Summary
<!-- What does this PR do? Link to the relevant ticket/sprint item. -->

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactor
- [ ] Documentation
- [ ] Infrastructure
- [ ] Clinical-adjacent (requires clinical QA sign-off)

## Test coverage
- [ ] Unit tests added/updated
- [ ] E2E tests added/updated (if user-facing change)
- [ ] All existing tests pass (`pnpm test` + `cd services/api && uv run pytest -q`)

## Clinical compliance checklist
<!-- If this PR doesn't touch clinical code, mark N/A -->
- [ ] N/A — no clinical-adjacent changes
- [ ] Crisis path is deterministic (no LLM calls, no network dependency)
- [ ] Relapse copy is compassion-first (no "failed" / "reset" framing)
- [ ] Clinical scores render in Latin digits regardless of locale
- [ ] No advertising SDK or session replay added
- [ ] PHI boundary (`X-Phi-Boundary: 1`) set on all PHI routes
- [ ] Audit log streams not mixed

## i18n
- [ ] N/A — no user-facing copy changes
- [ ] en.json catalog key(s) added
- [ ] fr/ar/fa keys added with `__NEEDS_REVIEW__` value (no machine translation)
- [ ] `_meta.status` remains `"draft"` in non-en catalogs

## Documentation
- [ ] N/A — no new subsystem or breaking change
- [ ] Relevant `Docs/Technicals/*.md` updated (Architecture, API spec, Data Model, etc.)

## Screenshots / recordings
<!-- For UI changes, attach before/after screenshots or a screen recording -->
