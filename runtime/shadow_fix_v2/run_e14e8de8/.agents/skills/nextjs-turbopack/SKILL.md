---
name: nextjs-turbopack
description: Next.js and Turbopack guidance for local development, incremental bundling, caching, and webpack fallback decisions.
origin: ECC
---

# Next.js and Turbopack

Use this skill when developing, debugging, or optimizing Next.js applications that use Turbopack or may need a webpack fallback.

## When to Activate

- Starting or debugging a Next.js dev server.
- Diagnosing slow startup, slow HMR, or bundler cache behavior.
- Deciding whether a Turbopack issue requires webpack fallback.
- Reviewing production bundle size or dependency splitting.
- Updating Next.js configuration related to bundling.

## Practical Guidance

- Recent Next.js versions use Turbopack by default for local development.
- Use the default dev bundler unless a specific plugin or bug requires fallback.
- Verify the project's installed Next.js version before relying on version-specific flags.
- Keep `.next` cache behavior in mind when diagnosing cold-start versus warm-start speed.
- Use official Next.js documentation for exact flags because fallback syntax can differ by version.

## Commands

```bash
npm run dev
npm run build
npm run start
```

For direct Next.js commands:

```bash
npx next dev
npx next build
npx next start
```

## Debug Checklist

- Confirm the installed Next.js version from `package.json` or `npm ls next`.
- Check whether `next.config.*` contains webpack-specific customizations.
- If dev startup is slow, compare first run versus second run to account for cache warming.
- If HMR is broken, isolate the smallest page/component that reproduces it.
- If a dependency behaves differently under Turbopack, test a webpack fallback and capture the exact error.

## Bundle Review

- Prefer server components where they reduce client bundle size.
- Avoid importing large client-only libraries into shared or server paths.
- Split heavy routes and widgets with dynamic imports where it improves user experience.
- Use the project's supported bundle analyzer tooling before making broad optimization changes.

## Review Checklist

- Version-specific assumptions were verified locally or against official docs.
- Fallback to webpack is tied to a concrete compatibility issue.
- Cache deletion is used as a diagnostic step, not as a permanent workflow.
- Bundle changes preserve behavior and are verified with build/test output.
