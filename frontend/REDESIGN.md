# CloudMind website redesign

## What changed

- Ivory, charcoal and burnt-orange visual system with refreshed navigation, footer and article cards.
- Homepage with a pointer-responsive Three.js globe, orbital labels, section entrances and animated career artwork.
- Motion pause control, system reduced-motion support and a static fallback when WebGL is unavailable.
- Real news feed with topic filters, search, pagination, loading placeholders and recoverable errors. Requests from a previous filter cannot replace the current results.
- Responsive mobile navigation, compact mobile chat launcher, keyboard focus styles and a skip link.
- Article, jobs, contact and admin routes remain connected to the existing backend. Navigating between routes resets the scroll position.

## Local preview

Use the existing local backend with `npm run dev`. To preview against the public news API without starting the backend, run from this directory in PowerShell:

```powershell
$env:DEV_API_TARGET = 'https://cloudmindai.in/api'
npm run dev -- --host 127.0.0.1
```

Open http://127.0.0.1:5000. The override only affects the development proxy. Production continues to use `/api`.

## Verification

- Production build passes. Three.js is loaded as a separate optional chunk; Vite reports its 531 kB minified size (132 kB gzip) as a size warning.
- ESLint passes for all changed JavaScript files. Full-project lint still reports five existing errors in Article.jsx, ContactUs.jsx and JobDetail.jsx, plus existing hook dependency warnings.
- All 12 existing URL assertions pass.
- Browser checks passed for real AI filtering, empty search, clearing filters, loading more articles, canonical article navigation, scroll reset, careers, contact and the mobile menu.
- Rendered pixels confirmed the globe moves, pauses and respects reduced motion. WebGL fallback and network-error retry were also checked. No runtime exceptions were observed.
- Desktop and mobile screenshots were inspected; the 320 px layout was checked for horizontal overflow.

The redesign is local. No production deployment was performed.
