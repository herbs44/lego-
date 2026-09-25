// usage: node steps.js <model.mpd (unter MODEL_DIR)> <jobs.json> <ausgabeordner>
// jobs.json: [{"name":"s001","show":[...],"fade":[...],"frame":[...],"az":30,"el":35,"w":1100,"h":800}, ...]
const fs = require('fs'), path = require('path');
const {chromium} = require(process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright');
(async () => {
  const [m, jf, out] = process.argv.slice(2);
  const jobs = JSON.parse(fs.readFileSync(jf, 'utf8'));
  fs.mkdirSync(out, {recursive: true});
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  const p = await b.newPage({viewport: {width: 1400, height: 1000}});
  await p.goto(`http://localhost:8765/steps.html?m=/model/${m}`);
  await p.waitForFunction('window.done===true', null, {timeout: 3600000});
  const errs = await p.evaluate('window.errors');
  if (errs.length) { console.log('errors', errs); process.exit(1); }
  console.log('groups', (await p.evaluate('window.groupNames')).length);
  let n = 0;
  for (const J of jobs) {
    const f = path.join(out, J.name + '.png');
    if (fs.existsSync(f) && !process.env.FORCE) { n++; continue; }
    await p.evaluate(j => window.job(j), J);
    await p.locator('canvas').screenshot({path: f});
    n++; if (n % 10 === 0) console.log('rendered', n, '/', jobs.length);
  }
  await b.close();
  console.log('fertig', n);
})();
