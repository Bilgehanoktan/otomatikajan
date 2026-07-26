# Frontend Cleanup Issue Map

Scope: apps/refine_control_plane

## Issues to track

| Phase | Issue title |
|---|---|
| A | [Frontend Cleanup] Resolve blocking lint errors permanently |
| B | [Frontend Cleanup] Remove unused imports and variables |
| C | [Frontend Cleanup] Escape JSX entities |
| D | [Frontend Cleanup] Fix image accessibility warnings |
| E | [Frontend Cleanup] Stabilize React hook dependencies |
| F1 | [Frontend Cleanup] Replace broad frontend types phase 1 |
| F2 | [Frontend Cleanup] Replace broad frontend types phase 2 |

## Test commands

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```
