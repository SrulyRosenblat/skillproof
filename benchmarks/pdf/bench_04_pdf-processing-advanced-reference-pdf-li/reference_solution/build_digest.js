const fs = require('fs');
const { PDFDocument, StandardFonts, rgb } = require('./lib/pdf-lib.min.js');

async function main() {
    const outDoc = await PDFDocument.create();

    const aBytes = fs.readFileSync('report_a.pdf');
    const aDoc = await PDFDocument.load(aBytes);
    const aPages = await outDoc.copyPages(aDoc, aDoc.getPageIndices());
    aPages.forEach(p => outDoc.addPage(p));

    const bBytes = fs.readFileSync('report_b.pdf');
    const bDoc = await PDFDocument.load(bBytes);
    const bPages = await outDoc.copyPages(bDoc, [0, 2]);
    bPages.forEach(p => outDoc.addPage(p));

    const font = await outDoc.embedFont(StandardFonts.Helvetica);
    const summaryPage = outDoc.addPage([612, 792]);
    summaryPage.drawText('Digest Summary', {
        x: 100,
        y: 700,
        size: 18,
        font,
        color: rgb(0, 0, 0)
    });

    const outBytes = await outDoc.save();
    fs.writeFileSync('digest.pdf', outBytes);
}

main();
