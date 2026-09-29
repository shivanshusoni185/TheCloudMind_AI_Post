# Finance section and latency review

## Content change

Financial news replaces the IPL topic button and has a homepage shortcut. It uses the existing `Finance` tag filter. Cricket stays available; existing IPL articles and backend support are retained for later. The assistant suggestion also points to financial news.

The public API returned no Finance-tagged articles on September 29, 2026. The section therefore shows an honest empty state. Publish an article with the `Finance` tag through the existing admin editor to populate it. Automatic financial-news collection has not been added.

## Changes made first

- Serve Space Grotesk and Source Serif 4 locally with `font-display: swap`. The fonts and their OFL licenses are in `public/fonts`; the blocking Google Fonts stylesheet is removed.
- Render the main headline immediately while keeping its movement animation.
- Start the optional 3D download only after page load, when the globe is near the viewport and the browser has idle time. Initial reduced-motion and data-saver visits use the static globe and skip the approximately 132 kB gzipped Three.js download.
- Stop the WebGL animation frame loop when off-screen, paused, hidden, or in reduced-motion mode. Resume when appropriate.
- Let below-the-fold news images load lazily instead of giving the first three high priority.
- Share overlapping identical news requests. Distinct filters stay independent, and completed or failed requests are removed so the next read can fetch fresh data.

## Measurements

Local production preview, 390 × 844 viewport, 4× CPU slowdown, 150 ms simulated network latency, 1.6 Mbps download, browser HTTP cache disabled, three runs per version. The news API was proxied to the live site. These are comparative lab measurements, not production Core Web Vitals or a guaranteed improvement for every visitor.

| Metric | Before | After |
| --- | --- | --- |
| Median first contentful paint | 1.164 s | 1.176 s |
| Median largest contentful paint | 1.724 s | 1.176 s |
| Initial article image bodies at this viewport | 140,896 bytes | 52,066 bytes |

LCP improved by approximately 32%; first paint was effectively unchanged. Keeping the headline visible removes its previous animation-related display delay. The typography change and loading changes were measured together, so the figures do not isolate each change's contribution.

Live-site spot checks from this workstation:

- HTML: approximately 0.78 s to first byte.
- Cached news list on a new connection: approximately 0.75 s, including approximately 0.51 s through TLS setup.
- The same news list over a reused connection: approximately 0.24 s.
- A Finance filter request over that reused connection: approximately 1.00 s; response was an empty list.
- One sampled image: 151,876 bytes, already served as a cache HIT.

## What to improve next, in order

1. **Network delivery:** verify CDN coverage and server location relative to readers. The repository's nginx comments describe a New York application server and Mumbai database; confirm the deployed locations before deciding whether to move services. Cached responses still pay the network round trip.
2. **Responsive article images:** add small WebP/AVIF thumbnail variants for cards while retaining larger article images. Current card images use the original image endpoint.
3. **Remaining data requests:** profile uncached filter queries and article detail responses. Keep existing nginx micro-caching and backend cache invalidation; do not add another cache without measuring what is already there.

No infrastructure changes or production deployment were made.

## References

The prioritization follows Google's guidance on [LCP resource and render delays](https://web.dev/articles/optimize-lcp) and [resource fetch priority](https://web.dev/articles/fetch-priority).
