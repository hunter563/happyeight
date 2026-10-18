// 直接调用 gin-18 和 LuckyDD 的源码纯函数，不启动其独立服务。
import fs from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const gin = await import(pathToFileURL(path.join(root, 'vendor/lottery-lab/src/utils/lottery-data.js')));
const rules = await import(pathToFileURL(path.join(root, 'vendor/lottery-lab/src/utils/lottery-rules.js')));
async function pureModule(file, boundary) {
  const source = fs.readFileSync(path.join(root, file), 'utf8');
  if (!source.includes(boundary)) throw new Error('上游接口发生变化');
  const pure = source.split(boundary)[0].replace(/^import \{ getAll \} from '\.\.\/database'\r?\n/m, '');
  return import('data:text/javascript;base64,' + Buffer.from(stripTypeScriptTypes(pure)).toString('base64'));
}
const stats = await pureModule('vendor/luckydd/backend/src/analysis/statistics.ts', 'export const getStatistics =');
const patterns = await pureModule('vendor/luckydd/backend/src/analysis/patternMining.ts', 'export const getPatterns =');
const fields = 'one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split(' ');
function analyze(draws, detail = true) {
  const rows = draws.map(d => d.numbers);
  const ginCounts = gin.countNumberInData(draws.map(d => Object.fromEntries(fields.map((f,i) => [f, String(d.numbers[i]).padStart(2,'0')]))));
  const hot = stats.calculateHotColdNumbers(rows, 80, 1);
  const counts = new Map(hot.map(x => [x.number, x]));
  // 上游遗漏函数最新命中为1且从未出现为0；统一为最新命中0、从未出现=窗口长度。
  const missing = stats.calculateMissingNumbers(rows, 80, 1).map(x => ({number:x.number, missing:counts.has(x.number) ? x.missingDays - 1 : rows.length}));
  const all = Array.from({length:80},(_,i) => counts.get(i+1) || {number:i+1,count:0,frequency:0,isHot:false,isCold:true});
  const correlations = patterns.findNumberCorrelations(rows,80,1);
  return {
    frequency:all, missing, ginCounts, correlations,
    sum: stats.calculateSumAnalysis(rows), parity: stats.calculateParityAnalysis(rows),
    intervals: stats.calculateIntervalAnalysis(rows, [1,21,41,61].map(start => ({start,end:start+19,label:`${start}–${start+19}`}))),
    patterns: detail ? patterns.findFrequentPatterns(rows,0.05) : []
  };
}
function calculate(o) {
  const k=o.k, selected=o.selected, hits=o.hits;
  if (![k,selected,hits].every(Number.isInteger) || k<1 || k>10 || selected<k || selected>80 || hits<0 || hits>Math.min(selected,20) || selected-hits>60) throw new Error('参数范围不合法');
  const counts=rules.calculateRegularPrizeCounts({playType:`pick${k}`,selectedCount:selected,hitCount:hits});
  const breakdown=counts.map(x=>({...x, amount:rules.getConfirmedPrizeAmount(`pick${k}`,x.hitSize), floating:rules.isFloatingPrize(`pick${k}`,x.hitSize)})).filter(x=>x.count>0);
  const stakes=rules.combine(selected,k);
  return {stakes,cost:rules.calculateStakeAmount(stakes,1),fixedPrize:breakdown.reduce((s,x)=>s+x.count*x.amount,0),floatingTickets:breakdown.filter(x=>x.floating).reduce((s,x)=>s+x.count,0),breakdown,notice:'奖金表沿用上游快照，未核验当前官方规则；浮动奖金未计入。仅用于规则演示。'};
}
let input=''; for await (const chunk of process.stdin) input+=chunk;
try {
  const request=JSON.parse(input);
  const result=request.op==='calc' ? calculate(request) : request.op==='batch' ? request.batches.map(d=>analyze(d,false)) : analyze(request.draws);
  process.stdout.write(JSON.stringify(result));
} catch(e) { process.stderr.write(String(e.message)); process.exitCode=1; }
