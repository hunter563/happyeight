/* Validate static app element references before deployment, no npm deps. */
const fs=require('node:fs');
const assert=require('node:assert/strict');
const app=fs.readFileSync('web/app.js','utf8');
const html=fs.readFileSync('web/index.html','utf8');
const ids=[...app.matchAll(/\$\('([^']+)'\)/g)].map(m=>m[1]);
const missing=[...new Set(ids)].filter(id=>!html.includes('id="'+id+'"'));
assert.deepEqual(missing,[], 'UI references missing DOM nodes');
assert.match(html,/src="\/vendor\/echarts\.min\.js"/);
assert.match(html,/src="\/app\.js"/);
assert.ok(html.indexOf('/vendor/echarts.min.js')<html.indexOf('/app.js'));
assert.match(html,/id="charts-family-view"/);
assert.match(html,/id="charts-heatmap"/);
process.stdout.write('UI wiring PASS ('+new Set(ids).size+' DOM references)\n');
