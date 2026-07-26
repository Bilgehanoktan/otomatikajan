# Frontend Cleanup Test Matrix

Date: 2026-06-12
Scope: apps/refine_control_plane

## Commands

Run after every cleanup phase:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```

## Phase Results

| Phase | Target | Commit | Test status |
|---|---|---|---|
| A | lint errors | 0f725efdb11014a989e49555514ed60ecb947a89 | needs runner |
| B | unused imports and variables | pending | needs runner |
| C | JSX text entities | pending | needs runner |
| D | image accessibility | pending | needs runner |
| E | React hook warnings | pending | needs runner |
| F | TypeScript model cleanup | pending | needs runner |

## Notes

The repository must be tested in GitHub Actions or a local machine with Node dependencies installed.
