## Summary
<!-- What does this PR do? Why? -->


## Type of change
- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 🎨 UI / styling
- [ ] ♻️ Refactor (no behaviour change)
- [ ] 🔧 Config / tooling
- [ ] 📝 Docs only

## Pre-deploy checklist

### General
- [ ] CI is green (all checks pass)
- [ ] No sensitive data, API keys or secrets committed

### Backend changes (if any)
- [ ] New endpoints are guarded correctly (auth / admin where needed)
- [ ] Database migrations added via Alembic if models changed (`alembic revision --autogenerate`)
- [ ] New dependencies added to `backend/requirements.txt`
- [ ] Existing tests still pass; new logic covered by tests

### Frontend changes (if any)
- [ ] `npm run build` completes without errors locally
- [ ] Tested in browser (Chrome + Firefox or Safari)
- [ ] New routes added to `router.js` with correct `meta` flags (`public`, `adminOnly`)
- [ ] No console errors or Vue warnings

### Game / Word Bank changes (if any)
- [ ] Guest access handled (`v-if="isLoggedIn"` guards where needed)
- [ ] Admin-only features protected on both frontend and backend

## Testing
<!-- Describe how you tested this. Include steps to reproduce if it's a bug fix. -->


## Screenshots (if UI change)
<!-- Before / after if applicable -->


## Related issues
<!-- Closes #issue_number -->
