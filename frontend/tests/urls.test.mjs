// Standalone tests for lib/urls.js — run with:  node tests/urls.test.mjs
// No test framework needed; exits non-zero on the first failure.
import { articlePath, jobPath, articleUrl, jobUrl, safeExternalUrl, jsonLdSafe } from '../src/lib/urls.js'

let passed = 0
function eq(actual, expected, name) {
  if (actual !== expected) {
    console.error(`FAIL  ${name}\n  expected: ${expected}\n  actual:   ${actual}`)
    process.exit(1)
  }
  console.log(`PASS  ${name}`)
  passed++
}

// Dates use the 15th at noon so local-timezone offset never flips the month.
eq(articlePath({ created_at: '2026-06-15T12:00:00', slug: 'my-story' }), '/news/2026/06/my-story', 'articlePath dated')
eq(jobPath({ posted_at: '2026-08-15T12:00:00', slug: 'my-role' }), '/jobs/2026/08/my-role', 'jobPath uses posted_at')
eq(jobPath({ created_at: '2026-03-15T12:00:00', slug: 'x' }), '/jobs/2026/03/x', 'jobPath falls back to created_at')
eq(articleUrl({ created_at: '2026-06-15T12:00:00', slug: 's' }), 'https://cloudmindai.in/news/2026/06/s', 'articleUrl origin')
eq(jobUrl({ posted_at: '2026-08-15T12:00:00', slug: 's' }), 'https://cloudmindai.in/jobs/2026/08/s', 'jobUrl origin')

// safeExternalUrl blocks non-http(s) schemes
eq(safeExternalUrl('https://x.com/apply'), 'https://x.com/apply', 'safeUrl allows https')
eq(safeExternalUrl('http://x.com'), 'http://x.com', 'safeUrl allows http')
eq(safeExternalUrl('javascript:alert(1)'), '#', 'safeUrl blocks javascript:')
eq(safeExternalUrl('data:text/html,x'), '#', 'safeUrl blocks data:')
eq(safeExternalUrl(undefined), '#', 'safeUrl blocks undefined')

// jsonLdSafe escapes < and > so "</script>" cannot break out
const out = jsonLdSafe({ d: 'a</script><script>b' })
eq(out.includes('</script>'), false, 'jsonLdSafe has no literal </script>')
eq(out.includes('\\u003c'), true, 'jsonLdSafe escapes <')

console.log(`\nAll ${passed} url tests passed.`)
