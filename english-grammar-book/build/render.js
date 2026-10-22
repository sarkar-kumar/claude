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
  await page.goto('file://' + path.resolve(input), { waitUntil: 'load' });
  await page.pdf({
    path: output,
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: true,
    margin: { top: '17mm', bottom: '16mm', left: '13mm', right: '13mm' },
    headerTemplate: `<div style="width:100%;font-family:'Liberation Sans',Arial,sans-serif;font-size:7.5px;color:#666;padding:0 13mm;display:flex;justify-content:space-between;">
      <span>English for Competitive Exams · with SAT, GRE &amp; GMAT</span><span>BCS · Bank · Admission</span></div>`,
    footerTemplate: `<div style="width:100%;font-family:'Liberation Sans',Arial,sans-serif;font-size:8px;color:#444;text-align:center;">
      <span class="pageNumber"></span></div>`,
  });
  await browser.close();
})();
