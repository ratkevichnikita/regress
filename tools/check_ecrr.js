const fs=require('fs');
const src=fs.readFileSync(__dirname+'/../test-ecrr.js','utf8');
const ITEMS=eval(src.match(/const ITEMS = (\[[\s\S]*?\n\];)/)[1].replace(/;$/,''));

// ключ из первоисточника: labs.psychology.illinois.edu/~rcfraley/measures/ecrritems.htm
const REF={anx:[1,18], avo:[19,36], rev:[9,11,20,22,26,27,28,29,30,31,33,34,35,36]};

let fail=0;
const ok=(c,m)=>{ console.log((c?'  ok  ':'ПРОВАЛ')+'  '+m); if(!c) fail++; };

ok(ITEMS.length===36,'36 пунктов');
ok(new Set(ITEMS.map(i=>i[0])).size===36,'номера не повторяются');
ok(ITEMS.every((i,k)=>i[0]===k+1),'номера идут подряд 1..36');
ok(ITEMS.filter(i=>i[1]==='anx').length===18 && ITEMS.filter(i=>i[1]==='avo').length===18,'по 18 пунктов на шкалу');
ok(ITEMS.every(i=>i[1]===(i[0]<=18?'anx':'avo')),'1–18 тревожность, 19–36 избегание');
const rev=ITEMS.filter(i=>i[2]).map(i=>i[0]);
ok(JSON.stringify(rev)===JSON.stringify(REF.rev),'обратные совпадают с первоисточником: '+rev.join(','));
ok(ITEMS.every(i=>typeof i[3]==='string' && i[3].length>15),'все формулировки на месте');

const mean=(from,to,v)=>{let s=0;for(const i of ITEMS)if(i[0]>=from&&i[0]<=to)s+=i[2]?8-v:v;return s/18;};
const nrA=16,nrV=6; // прямых пунктов в каждой шкале
const cases=[
 [1, (nrA*1+2*7)/18, (nrV*1+12*7)/18],
 [4, 4, 4],
 [7, (nrA*7+2*1)/18, (nrV*7+12*1)/18],
];
console.log('\n  ответ   тревожность        избегание');
for(const [v,ea,ev] of cases){
  const a=mean(1,18,v), b=mean(19,36,v);
  const good=Math.abs(a-ea)<1e-9 && Math.abs(b-ev)<1e-9;
  console.log(`  все ${v}   ${a.toFixed(3)} (ждём ${ea.toFixed(3)})   ${b.toFixed(3)} (ждём ${ev.toFixed(3)})  ${good?'ok':'ПРОВАЛ'}`);
  if(!good) fail++;
}
const sym=[1,2,3,4,5,6,7].every(v=>Math.abs(mean(1,18,v)+mean(1,18,8-v)-8)<1e-9 && Math.abs(mean(19,36,v)+mean(19,36,8-v)-8)<1e-9);
console.log('');
ok(sym,'симметрия: среднее(v) + среднее(8−v) = 8 для всех v');
console.log(fail?`\nОШИБОК: ${fail}`:'\nВсё сошлось.');
process.exit(fail?1:0);
