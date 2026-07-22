#!/bin/bash
# Computes /workspace/output.docx from /workspace/data.json and
# /workspace/logo.png using the docx (docx-js) library, working around its
# defaults: A4 page size, a table grid that stays a meaningless placeholder
# unless the table (not just the cells) is also given column widths, SOLID
# header shading that renders as black, "bulleted" paragraphs that are
# really just literal bullet characters, and an embedded image saved with no
# recognized file extension unless its type is declared.
set -euo pipefail

node <<'JS'
const fs = require("fs");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  Table,
  TableRow,
  TableCell,
  WidthType,
  ShadingType,
  LevelFormat,
  AlignmentType,
  ImageRun,
} = require("docx");

const data = JSON.parse(fs.readFileSync("/workspace/data.json", "utf8"));
const logoBuffer = fs.readFileSync("/workspace/logo.png");

const COL_WIDTHS_DXA = [2880, 2160, 4320]; // 2in, 1.5in, 3in
const HEADER_FILL = "D9D9D9";

const headerRow = new TableRow({
  children: ["Metric", "Value", "Notes"].map(
    (text, i) =>
      new TableCell({
        width: { size: COL_WIDTHS_DXA[i], type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: HEADER_FILL, color: "auto" },
        children: [new Paragraph({ children: [new TextRun({ text, bold: true })] })],
      })
  ),
});

const bodyRows = data.metrics.map(
  (m) =>
    new TableRow({
      children: [m.metric, m.value, m.notes].map(
        (text, i) =>
          new TableCell({
            width: { size: COL_WIDTHS_DXA[i], type: WidthType.DXA },
            children: [new Paragraph({ children: [new TextRun(String(text))] })],
          })
      ),
    })
);

const table = new Table({
  columnWidths: COL_WIDTHS_DXA,
  width: { size: COL_WIDTHS_DXA.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  rows: [headerRow, ...bodyRows],
});

const takeawayParagraphs = data.takeaways.map(
  (text) =>
    new Paragraph({
      text,
      numbering: { reference: "takeaways-bullets", level: 0 },
    })
);

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "takeaways-bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
    ],
  },
  styles: {
    default: {
      document: { run: { font: "Arial", size: 24 } },
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "000000" },
        paragraph: {
          spacing: { before: 240, after: 240 },
          outlineLevel: 0,
        },
      },
    ],
  },
  sections: [
    {
      properties: {
        page: { size: { width: 12240, height: 15840 } },
      },
      children: [
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun(data.report_title)],
        }),
        new Paragraph({
          children: [
            new ImageRun({
              type: "png",
              data: logoBuffer,
              transformation: { width: 144, height: 72 },
              altText: {
                title: "Acme Corp Logo",
                description: "Acme Corp company logo",
                name: "AcmeLogo",
              },
            }),
          ],
        }),
        table,
        new Paragraph({ text: "" }),
        ...takeawayParagraphs,
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("/workspace/output.docx", buffer);
  console.log("wrote /workspace/output.docx");
});
JS
