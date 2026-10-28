// Converte o HTML do relatório em PDF com o Chromium do Playwright, esperando
// o MathJax terminar de desenhar as fórmulas.
// Uso: node imprimir_pdf.js <entrada.html> <saida.pdf>
const path = require("path");
const { chromium } = require("playwright");

(async () => {
  const [entrada, saida] = process.argv.slice(2);
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage();
  await pagina.goto("file://" + path.resolve(entrada), { waitUntil: "load" });
  await pagina.waitForFunction(
    () => window.MathJax && MathJax.startup && MathJax.startup.promise,
    null, { timeout: 30000 });
  await pagina.evaluate(() => MathJax.startup.promise);
  await pagina.pdf({
    path: saida,
    preferCSSPageSize: true,
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: "<span></span>",
    footerTemplate:
      '<div style="width:100%;text-align:center;font-size:8pt;color:#52514e;' +
      'font-family:Liberation Sans,sans-serif"><span class="pageNumber"></span>' +
      ' / <span class="totalPages"></span></div>',
  });
  await navegador.close();
})().catch((erro) => {
  console.error(erro);
  process.exit(1);
});
