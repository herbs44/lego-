// usage: node shoot.js <modelfile-in-MODEL_DIR> <outprefix> '<json views>'
const {chromium}=require('/opt/node22/lib/node_modules/playwright');
(async()=>{
  const [m,out,vj]=process.argv.slice(2); const views=JSON.parse(vj);
  const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const p=await b.newPage({viewport:{width:1400,height:1000}});
  p.on('console',msg=>{if(msg.type()==='error'||msg.type()==='warning')console.log('CONSOLE',msg.text().slice(0,200))});
  await p.goto(`http://localhost:8765/?m=/model/${m}`);
  await p.waitForFunction('window.done===true',null,{timeout:1800000});
  console.log('errors',await p.evaluate('window.errors'),'bbox',JSON.stringify(await p.evaluate('window.bbox')));
  for(const [name,v] of Object.entries(views)){
    await p.evaluate(v=>window.setView(...v),v);
    await p.locator('canvas').screenshot({path:`${out}_${name}.png`});
  }
  await b.close();
})();
