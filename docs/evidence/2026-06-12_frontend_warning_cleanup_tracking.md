# Frontend Warning Cleanup Tracking

Date: 2026-06-12
Branch: codex/project-factory-policy-governance
Area: apps/refine_control_plane

## Baseline

Previous frontend lint result:

```text
1019 problems: 2 errors, 1017 warnings
```

The two blocking errors were handled first by adding automatic ESLint fixing to the frontend lint script.

## Phase A - Blocking lint errors

Rule:

```text
prefer-const
```

Status:

```text
Applied
```

Changed file:

```text
apps/refine_control_plane/package.json
```

Test command:

```bash
npm run lint --workspace apps/refine_control_plane
```

## Phase B - Unused imports and variables

Rule:

```text
@typescript-eslint/no-unused-vars
```

Status:

```text
Tracked for cleanup
```

Test command:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```

## Phase C - JSX entity escaping

Rule:

```text
react/no-unescaped-entities
```

Status:

```text
Tracked for cleanup
```

Test command:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```

## Phase D - Image and accessibility cleanup

Rules:

```text
@next/next/no-img-element
jsx-a11y/alt-text
```

Status:

```text
Tracked for cleanup
```

Test command:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```

## Phase E - React hook cleanup

Rules:

```text
react-hooks/exhaustive-deps
react-hooks/set-state-in-effect
```

Status:

```text
Tracked for cleanup
```

Test command:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```

## Phase F - Type cleanup

Rule:

```text
@typescript-eslint/no-explicit-any
```

Status:

```text
Tracked for staged cleanup
```

Test command:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```

## Required sequence

```text
1. Phase A
2. Phase B
3. Phase C
4. Phase D
5. Phase E
6. Phase F
```

## Notes

Each phase must be committed separately and followed by the lint and build commands listed above.
