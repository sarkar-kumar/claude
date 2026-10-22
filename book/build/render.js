// Render an HTML file to an A4 PDF with headless Chromium (Playwright).
// Usage: node render.js input.html output.pdf
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }

(async () => {
  const [input, output] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(input), { waitUntil: 'load', timeout: 0 });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: output,
    format: 'A4',
    printBackground: true,
    outline: true,
    tagged: true,
    displayHeaderFooter: true,
    margin: { top: '16mm', bottom: '15mm', left: '12mm', right: '12mm' },
    headerTemplate: `<div style="width:100%;font-family:'Liberation Sans',Arial,sans-serif;font-size:7.5px;color:#666;padding:0 12mm;display:flex;justify-content:space-between;">
      <span>English for Competitive Exams · BCS · Bank · Admission · SAT · GRE · GMAT</span><span>Grammar · Vocabulary · Literature</span></div>`,
    footerTemplate: `<div style="width:100%;font-family:'Liberation Sans',Arial,sans-serif;font-size:8px;color:#444;text-align:center;">
      <span class="pageNumber"></span></div>`,
    timeout: 0,
  });
  await browser.close();
})();
