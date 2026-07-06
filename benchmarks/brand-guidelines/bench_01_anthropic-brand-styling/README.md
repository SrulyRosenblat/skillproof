# Anthropic Brand Styling Benchmark

This benchmark tests whether an agent can apply Anthropic brand styling to a deterministic SVG deliverable: the correct color palette, heading/body font split, contrast-aware text colors, and the documented accent-color cycle for non-text shapes.

That matters for this skill because the key value is not generic "make it look branded." The skill encodes specific brand constants and usage rules: exact hex colors, exact font stacks with fallbacks, headings switching at 24pt and above, and accent shapes rotating through orange, blue, and green. A model that has actually mastered the skill should produce those details reliably from the brand request alone.

## Task Shape

The agent receives one fixture, [`files/brief.json`](files/brief.json), and must create:

- `/workspace/poster.svg`
- `/workspace/style-summary.json`

The prompt fixes the layout and content placement so grading can focus on the styling capability instead of layout creativity. The agent still has to supply the Anthropic brand choices correctly.

## Grading

`grader/grade.sh` runs `pytest` checks over the final `/workspace` state only.

The grader verifies:

- `poster.svg` exists and is exactly `1200x900`
- the required banner, cards, footer strip, and decorative circles exist at the exact required coordinates
- all required text from `brief.json` appears exactly once in SVG document order
- every text node exposes explicit `font-family`, `font-size`, and `fill` attributes
- text at size `24` or larger uses `Poppins, Arial, sans-serif`
- text below `24` uses `Lora, Georgia, serif`
- dark panels use the light Anthropic text color for their text
- light panels use the dark Anthropic text color for their text
- the three decorative circles use Anthropic accent colors in left-to-right order: orange, blue, green
- `style-summary.json` matches the required schema and exactly reflects the SVG text nodes, palette, and font-family strings

These checks are all traceable to explicit statements in `task_prompt.md`.

## Reference Solution

The reference solution in [`reference_solution/`](reference_solution) satisfies the benchmark by:

- using Anthropic main colors `#141413`, `#faf9f5`, and `#e8e6dc` in the SVG
- declaring the Anthropic font stacks exactly as required
- assigning heading styling to the title, section headings, and quote because each is `24` or larger
- assigning body styling to the subtitle, bullets, and attribution because each is below `24`
- using light text on the dark banner and footer strip, and dark text on the light cards
- cycling the decorative circles through `#d97757`, `#6a9bcc`, and `#788c5d`
- emitting a `style-summary.json` that matches the SVG contents exactly

## Local Validation

The benchmark was validated locally in two states:

- fixtures plus reference outputs: `grader/grade.sh` passed
- fixtures alone: `grader/grade.sh` failed
