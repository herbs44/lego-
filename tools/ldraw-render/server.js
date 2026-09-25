const http=require('http'),fs=require('fs'),path=require('path'),https=require('https');
const ROOT=__dirname, CACHE=path.join(ROOT,'cache'); fs.mkdirSync(CACHE,{recursive:true});
const UP='https://raw.githubusercontent.com/gkjohnson/ldraw-parts-library/master/complete/ldraw/';
const inflight={};
function fetchUp(rel){
  if(inflight[rel]) return inflight[rel];
  return inflight[rel]=new Promise(res=>{
    const tryGet=(n)=>https.get(UP+rel.split('/').map(encodeURIComponent).join('/'),r=>{
      if(r.statusCode===404){r.resume();return res(404);}
      if(r.statusCode!==200){r.resume(); if(n>0) return setTimeout(()=>tryGet(n-1),1000); return res(null);}
      const ch=[];r.on('data',d=>ch.push(d));r.on('end',()=>res(Buffer.concat(ch)));
    }).on('error',()=>{ if(n>0) setTimeout(()=>tryGet(n-1),1000); else res(null);})
      .setTimeout(20000,function(){this.destroy(new Error('timeout'));});
    tryGet(3);
  });
}
const MIME={'.js':'text/javascript','.html':'text/html','.mpd':'text/plain','.ldr':'text/plain','.dat':'text/plain'};
http.createServer(async (req,res)=>{
  console.log('REQ',req.url);
  let u=decodeURIComponent(req.url.split('?')[0]);
  if(u.startsWith('/ldraw/')){
    const rel=u.slice(7).toLowerCase(); const cf=path.join(CACHE,rel.replace(/\//g,'__'));
    if(fs.existsSync(cf)){res.writeHead(200);return res.end(fs.readFileSync(cf));}
    if(fs.existsSync(cf+'.404')){res.writeHead(404);return res.end();}
    const b=await fetchUp(rel);
    if(b===404){fs.writeFileSync(cf+'.404','');res.writeHead(404);return res.end();}
    if(!b){delete inflight[rel];console.log('FAIL',rel);res.writeHead(503);return res.end();}
    fs.writeFileSync(cf,b);res.writeHead(200);return res.end(b);
  }
  let f=path.join(ROOT,u==='/'?'index.html':u);
  if(u.startsWith('/model/')) f=path.join(process.env.MODEL_DIR||ROOT,u.slice(7));
  if(!fs.existsSync(f)){res.writeHead(404);return res.end();}
  res.writeHead(200,{'Content-Type':MIME[path.extname(f)]||'application/octet-stream'});res.end(fs.readFileSync(f));
}).listen(8765,()=>console.log('up'));
process.on('uncaughtException',e=>console.log('UNCAUGHT',e&&e.stack));
process.on('unhandledRejection',e=>console.log('UNHANDLED',e&&e.stack));
