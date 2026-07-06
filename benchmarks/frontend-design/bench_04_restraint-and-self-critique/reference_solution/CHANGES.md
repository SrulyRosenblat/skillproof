# Changes from the draft

## What I removed

The draft had five things competing for attention at once. I cut four of them
entirely:

- The bouncing "WARBLE PRESS" logo — gone. The wordmark is now static type.
- The scrolling ticker strip — gone. Its facts (40+ labels, 500/day, 6-week
  turnaround, 100 minimum) now live in a plain, still stat row instead of a
  looping marquee.
- The falling confetti — gone entirely, it wasn't tied to anything the client
  actually does.
- The animated rainbow background on the hero — gone. The hero is now a quiet
  paper-colored background with one rust-red accent.

## What I kept as the one signature moment

I replaced the pulsing/glowing "Get a quote" button with a new single moment: a
small hand-cut lacquer groove (element id `lathe-groove`, a circle of fine
concentric rings, the shape of the actual grooves this shop cuts) that spirals
inward once when the page loads, right under the headline. It's the one thing on the page that moves, it's the
one saturated color accent, and it's a literal picture of the thing that makes
this shop different — someone still cutting lacquers by hand on a 1978 lathe —
rather than a generic UI flourish. Everything else on the page holds still.

## Accessibility and device fixes

- **Phone layout:** added the mobile viewport meta tag and a `max-width: 600px`
  breakpoint that reflows the stat row from four columns to two and shrinks the
  groove graphic, so nothing requires sideways scrolling on a 375px screen.
- **Keyboard focus:** removed the draft's blanket `outline: none`. Links and the
  quote button now get a solid 3px focus ring in the accent color via
  `:focus-visible`, so keyboard users can always see what's focused.
- **Motion sensitivity:** the lacquer-groove animation is wrapped in a
  `prefers-reduced-motion: reduce` query that holds it in its finished state
  instead of animating, for anyone who has that preference set. There is no
  other looping animation left on the page.
