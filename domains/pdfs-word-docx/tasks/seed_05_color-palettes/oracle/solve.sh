#!/bin/bash
# Builds /workspace/deck.pptx from scratch: a two-slide deck where slide 1 is
# styled with Anthropic's own official brand colors (light background, dark
# title text, three accent swatches in primary/secondary/tertiary accent
# order) and slide 2 is styled with the "Coral Energy" presentation color
# palette (primary background, secondary content block, accent title text).
set -euo pipefail

python3 - <<'PY'
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

DECK_PATH = "/workspace/deck.pptx"

# Anthropic's official brand colors.
BRAND_LIGHT = RGBColor(0xFA, 0xF9, 0xF5)
BRAND_DARK = RGBColor(0x14, 0x14, 0x13)
BRAND_ACCENT_PRIMARY = RGBColor(0xD9, 0x77, 0x57)
BRAND_ACCENT_SECONDARY = RGBColor(0x6A, 0x9B, 0xCC)
BRAND_ACCENT_TERTIARY = RGBColor(0x78, 0x8C, 0x5D)

# The "Coral Energy" presentation-design color palette.
CORAL_PRIMARY = RGBColor(0xF9, 0x61, 0x67)
CORAL_SECONDARY = RGBColor(0xF9, 0xE7, 0x95)
CORAL_ACCENT = RGBColor(0x2F, 0x3C, 0x7E)

prs = Presentation()
blank_layout = prs.slide_layouts[6]

# --- Slide 1: "About Anthropic" ---
slide1 = prs.slides.add_slide(blank_layout)
slide1.background.fill.solid()
slide1.background.fill.fore_color.rgb = BRAND_LIGHT

title_box = slide1.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(9), Inches(1.2))
tf = title_box.text_frame
tf.text = "About Anthropic"
title_run = tf.paragraphs[0].runs[0]
title_run.font.size = Pt(36)
title_run.font.color.rgb = BRAND_DARK

body_box = slide1.shapes.add_textbox(Inches(0.5), Inches(1.8), Inches(9), Inches(1.5))
body_box.text_frame.text = "Building safe and beneficial AI systems."

accent_specs = [
    ("AccentOne", BRAND_ACCENT_PRIMARY, Inches(0.5)),
    ("AccentTwo", BRAND_ACCENT_SECONDARY, Inches(3.5)),
    ("AccentThree", BRAND_ACCENT_TERTIARY, Inches(6.5)),
]
for name, color, left in accent_specs:
    shape = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, Inches(4), Inches(2), Inches(1))
    shape.name = name
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()

# --- Slide 2: "Our Partnership Vision" ---
slide2 = prs.slides.add_slide(blank_layout)
slide2.background.fill.solid()
slide2.background.fill.fore_color.rgb = CORAL_PRIMARY

title_box2 = slide2.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(9), Inches(1.2))
tf2 = title_box2.text_frame
tf2.text = "Our Partnership Vision"
title_run2 = tf2.paragraphs[0].runs[0]
title_run2.font.size = Pt(36)
title_run2.font.color.rgb = CORAL_ACCENT

secondary_block = slide2.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(2.2), Inches(9), Inches(3)
)
secondary_block.name = "SecondaryBlock"
secondary_block.fill.solid()
secondary_block.fill.fore_color.rgb = CORAL_SECONDARY
secondary_block.line.fill.background()

prs.save(DECK_PATH)
print("wrote", DECK_PATH)
PY
