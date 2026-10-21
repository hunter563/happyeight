/* Optional real-browser check: install Playwright + Chromium, then run this file.
 * Uses a temporary database. Synthetic fixtures never enter the app database.
 * LOTTERY_SCREENSHOT_DIR optionally saves initial, real KL8 snapshot views.
 */
const {chromium} = require('playwright');
const {spawn} = require('node:child_process');
const {mkdtempSync, rmSync, mkdirSync} = require('node:fs');
const {tmpdir} = require('node:os');
const {join, resolve} = require('node:path');
const assert = require('node:assert/strict');
const root=resolve(__dirname,'..'), temp=mkdtempSync(join(tmpdir(),'eight-lottery-'));
const code=`from fusion.data import Store
from fusion.server import make_handler
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
store=Store(Path(sys.argv[1]));store.seed()
server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(store,'',''))
print('READY:'+str(server.server_port),flush=True)
server.serve_forever()`;
const server=spawn(process.env.PYTHON || 'python',['-c',code,join(temp,'browser.sqlite')],{cwd:root,stdio:['ignore','pipe','pipe']});
let browser, logs='';server.stderr.on('data',data=>{logs+=data;});
const examples={ssq:[[33,5,4,3,2,1],[1]],fc3d:[[0,0,1],[]],qlc:[[1,2,3,4,5,6,7],[30]],dlt:[[1,2,3,4,35],[1,12]],pl3:[[0,0,0],[]],pl5:[[0,0,1,1,9],[]],qxc:[[0,0,1,2,3,9],[14]]};
const names={ssq:'双色球',fc3d:'福彩3D',qlc:'七乐彩',dlt:'大乐透',pl3:'排列3',pl5:'排列5',qxc:'七星彩'};
const source='浏览器测试合成数据（非真实开奖）<img src=x onerror=alert(1)>';
async function loaded(page){await page.waitForFunction(()=>!document.body.classList.contains('loading') && document.querySelector('#window-count').textContent!=='—');}
async function choose(page,game){await page.locator(`[data-game="${game}"]`).click();await loaded(page);}
(async()=>{
  const port=await new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>reject(new Error('Server startup timed out: '+logs)),20000);
    server.once('error',reject);server.once('exit',code=>reject(new Error('Server exited '+code+': '+logs)));
    server.stdout.on('data',data=>{const m=String(data).match(/READY:(\d+)/);if(m){clearTimeout(timeout);resolve(Number(m[1]));}});
  });
  browser=await chromium.launch({headless:true,args:['--no-sandbox'],...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{})});
  const context=await browser.newContext({viewport:{width:1440,height:1040}});
  const page=await context.newPage(),errors=[];
  page.on('pageerror',error=>errors.push(String(error)));
  await page.goto(`http://127.0.0.1:${port}/lotteries`);await loaded(page);
  assert.equal(await page.locator('[data-game]').count(),8);
  assert.equal(await page.locator('#game-title').textContent(),'快乐8');
  assert.equal(await page.locator('#distribution-table tbody tr').count(),50);
  assert.equal(await page.locator('#distribution-table thead th').count(),83);
  const screenshots=process.env.LOTTERY_SCREENSHOT_DIR;
  if(screenshots){mkdirSync(screenshots,{recursive:true});await page.screenshot({path:join(screenshots,'eight-lottery-desktop.png'),fullPage:true});}
  await page.setViewportSize({width:390,height:844});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile document overflows');
  if(screenshots)await page.screenshot({path:join(screenshots,'eight-lottery-mobile.png'),fullPage:true});
  await page.setViewportSize({width:1440,height:1040});
  for(const [game,[primary,secondary]] of Object.entries(examples)){
    await choose(page,game);
    assert.equal(await page.locator('#game-title').textContent(),names[game]);
    assert(await page.locator('#empty').isVisible());
    await page.locator('#open-import').click();
    await page.locator('#source').fill(source);
    await page.locator('#import-file').setInputFiles({name:`${game}.json`,mimeType:'application/json',buffer:Buffer.from(JSON.stringify({game,draws:[{game,issue:'2026001',date:'2026-01-01',primary,secondary}]}))});
    await page.waitForFunction(()=>document.querySelector('#import-status').textContent.includes('新增1期'));
    await page.waitForFunction(()=>!document.querySelector('#import-file').disabled);
    await loaded(page);
    assert.equal(await page.locator('#window-count').textContent(),'1');
    assert.equal(await page.locator('#latest-source img').count(),0,'Source must be text, not HTML');
    assert((await page.locator('#latest-source').textContent()).includes('<img'));
    await page.locator('[data-view="frequency"]').click();
    assert((await page.locator('.frequency-card').count())>0);
    await page.locator('[data-view="trend"]').click();
    assert.equal(await page.locator('#line-chart svg').count(),1);
    await page.locator('[data-view="history"]').click();
    assert.equal(await page.locator('#history-body tr').count(),1);
    assert.equal(await page.locator('#history-body img').count(),0);
    await page.locator('#field').selectOption('primary:0');await loaded(page);
    await page.locator('[data-view="distribution"]').click();
    assert.equal(await page.locator('#distribution-table tbody .hit').count(),1);
    if(game==='qxc'){
      await page.locator('#field').selectOption('secondary');await loaded(page);
      assert.equal(await page.locator('#latest-balls .secondary').textContent(),'14');
      assert.equal(await page.locator('#distribution-table thead th').count(),18);
      await page.locator('#version').selectOption('legacy');await loaded(page);
      assert(await page.locator('#empty').isVisible());
    }
  }
  await choose(page,'pl3');
  await page.locator('#field').selectOption('primary');await loaded(page);
  assert.equal(await page.locator('#distribution-table .multi').textContent(),'0×3');
  await page.locator('#from').fill('26002');await page.locator('#to').fill('26001');await page.locator('#filters button').click();
  await page.waitForFunction(()=>document.querySelector('#message').textContent.includes('起始期号不能晚于'));
  assert(!(await page.locator('#analysis').isVisible()),'Invalid query must not display stale chart');
  // Export/import round trip with duplicate handling.
  const exportData=await (await context.request.get(`http://127.0.0.1:${port}/api/lotteries/pl3/export`)).json();
  const duplicate=await context.request.post(`http://127.0.0.1:${port}/api/lotteries/pl3/import`,{data:exportData});
  assert.equal((await duplicate.json()).duplicates,1);
  await page.setViewportSize({width:390,height:844});await choose(page,'fc3d');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Populated mobile page overflows');
  assert.deepEqual(errors,[]);
  console.log('PASS: 8-game navigation, seven UI imports, preserved zeroes/repeats, charts, QXC versions, export roundtrip, XSS escaping, invalid range, mobile overflow, no JS errors.');
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{
  if(browser)await browser.close();
  server.kill();
  await new Promise(resolve=>server.exitCode!==null?resolve():server.once('exit',resolve));
  rmSync(temp,{recursive:true,force:true});
});
