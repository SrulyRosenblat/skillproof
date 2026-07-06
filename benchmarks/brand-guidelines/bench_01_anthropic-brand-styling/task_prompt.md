Create two files in `/workspace` using the content from `/workspace/brief.json`:

1. `/workspace/poster.svg`
2. `/workspace/style-summary.json`

The deliverable is a static SVG poster styled with the Anthropic brand guidelines available in your environment.

SVG requirements:

- The root `<svg>` must be exactly `1200` pixels wide and `900` pixels tall.
- Draw a full-canvas background rectangle.
- Draw a top banner rectangle at `x=0`, `y=0`, `width=1200`, `height=220`.
- Draw three section cards at these exact positions, each with `width=320` and `height=260`:
  - card 1: `x=80`, `y=300`
  - card 2: `x=440`, `y=300`
  - card 3: `x=800`, `y=300`
- Draw a footer quote strip at `x=80`, `y=620`, `width=1040`, `height=170`.
- Draw exactly three decorative circles with radius `22` centered at:
  - `(240, 255)`
  - `(600, 255)`
  - `(960, 255)`
- The three decorative circles are non-text accent shapes and must use the Anthropic accent colors in their documented cycle order from left to right.
- Use the text from `/workspace/brief.json` exactly once each:
  - title
  - subtitle
  - the three section headings
  - the six bullet lines
  - quote
  - attribution
- Every text element with font size `24` or larger must use the Anthropic heading font family with its documented fallback.
- Every text element with font size smaller than `24` must use the Anthropic body font family with its documented fallback.
- Put explicit `font-family`, `font-size`, and `fill` attributes on every `<text>` element so they can be inspected directly in the SVG.
- Choose text colors to match the Anthropic guidance for dark versus light backgrounds:
  - text placed on dark-filled panels must use the light brand text color
  - text placed on light-filled panels must use the dark brand text color

Content placement requirements:

- Title: font size `44`, placed inside the top banner.
- Subtitle: font size `20`, placed inside the top banner below the title.
- Each section heading: font size `28`, placed inside its card.
- Each bullet line: font size `18`, placed inside its card below the heading.
- Quote: font size `30`, placed inside the footer quote strip.
- Attribution: font size `18`, placed inside the footer quote strip below the quote.

`/workspace/style-summary.json` requirements:

- It must be valid JSON.
- It must contain exactly these top-level keys:
  - `heading_font`
  - `body_font`
  - `main_colors`
  - `accent_cycle`
  - `text_elements`
- `heading_font` must be the exact font-family string used for heading-sized text in the SVG.
- `body_font` must be the exact font-family string used for body-sized text in the SVG.
- `main_colors` must be an object with exactly these keys: `dark`, `light`, `mid_gray`, `light_gray`.
- `accent_cycle` must be a 3-item array listing the decorative circle colors in left-to-right order.
- `text_elements` must be an array in SVG document order. Each item must be an object with exactly these keys:
  - `text`
  - `font_size`
  - `font_family`
  - `fill`
- Each `text_elements` entry must match one `<text>` node in the SVG exactly.

Do not create any other required output files. Extra files are allowed, but the two files above must exist and satisfy this format.
