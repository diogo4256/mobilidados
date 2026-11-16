// Print an HTML page to an A4 PDF with a footer (title, page number). Usage: node pdf.js PAGE.html OUT.pdf "FOOTER"
// Needs Playwright with a Chromium (`npm i playwright && npx playwright install chromium` where none is installed).
const { chromium } = require('playwright');
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
(async () => {
  const [page, out, footer] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + page, { waitUntil: 'networkidle' });
  await p.pdf({
    path: out, format: 'A4', printBackground: true, preferCSSPageSize: true, displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:7pt;color:#6b7280;width:100%;padding:0 17mm;display:flex;justify-content:space-between">'
      + `<span>${esc(footer || '')}</span><span class="pageNumber"></span></div>`,
  });
  await b.close();
})();
