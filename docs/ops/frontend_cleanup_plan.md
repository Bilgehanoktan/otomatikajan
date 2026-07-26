# Frontend Cleanup Plan

Scope: `apps/refine_control_plane`

## Phase A

Fix lint errors first.

Test:

```bash
npm run lint --workspace apps/refine_control_plane
```

## Phase B

Remove unused imports and unused variables.

Test:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```

## Phase C

Escape JSX text entities.

Test:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```

## Phase D

Fix image accessibility warnings.

Test:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```

## Phase E

Stabilize React hook dependency warnings.

Test:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```

## Phase F

Replace broad frontend types gradually.

Test:

```bash
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
```

## Rule

Each phase must have its own commit and evidence note.
