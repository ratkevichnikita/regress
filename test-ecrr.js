const ITEMS = [
  [1,'anx',0,'Я боюсь потерять любовь партнёра.'],
  [2,'anx',0,'Я часто беспокоюсь, что партнёр не захочет остаться со мной.'],
  [3,'anx',0,'Я часто беспокоюсь, что партнёр на самом деле меня не любит.'],
  [4,'anx',0,'Я беспокоюсь, что буду дорожить партнёром сильнее, чем он мной.'],
  [5,'anx',0,'Мне часто хочется, чтобы чувства партнёра ко мне были такими же сильными, как мои к нему.'],
  [6,'anx',0,'Я много тревожусь по поводу своих отношений.'],
  [7,'anx',0,'Когда партнёра нет рядом, я беспокоюсь, что он может увлечься кем-то другим.'],
  [8,'anx',0,'Когда я показываю свои чувства партнёру, я боюсь, что он не почувствует того же ко мне.'],
  [9,'anx',1,'Я редко беспокоюсь о том, что партнёр меня оставит.'],
  [10,'anx',0,'Рядом с партнёром я начинаю сомневаться в себе.'],
  [11,'anx',1,'Я нечасто тревожусь о том, что меня бросят.'],
  [12,'anx',0,'Мне кажется, что партнёр не хочет такой близости, какой хочу я.'],
  [13,'anx',0,'Иногда чувства партнёра ко мне меняются без видимой причины.'],
  [14,'anx',0,'Моё желание быть очень близко иногда отпугивает людей.'],
  [15,'anx',0,'Я боюсь, что когда партнёр узнает меня по-настоящему, я ему не понравлюсь.'],
  [16,'anx',0,'Меня злит, что я не получаю от партнёра нужных мне тепла и поддержки.'],
  [17,'anx',0,'Я беспокоюсь, что окажусь хуже других.'],
  [18,'anx',0,'Мне кажется, партнёр замечает меня, только когда я злюсь.'],
  [19,'avo',0,'Я предпочитаю не показывать партнёру, что на самом деле чувствую.'],
  [20,'avo',1,'Мне комфортно делиться с партнёром личными мыслями и чувствами.'],
  [21,'avo',0,'Мне трудно позволить себе зависеть от партнёра.'],
  [22,'avo',1,'Мне очень комфортно быть близко с партнёром.'],
  [23,'avo',0,'Мне некомфортно открываться партнёру.'],
  [24,'avo',0,'Я предпочитаю не сближаться с партнёром слишком сильно.'],
  [25,'avo',0,'Мне становится не по себе, когда партнёр хочет большой близости.'],
  [26,'avo',1,'Мне довольно легко сближаться с партнёром.'],
  [27,'avo',1,'Мне несложно быть близко с партнёром.'],
  [28,'avo',1,'Обычно я обсуждаю с партнёром свои проблемы и тревоги.'],
  [29,'avo',1,'Когда мне тяжело, обратиться к партнёру помогает.'],
  [30,'avo',1,'Я рассказываю партнёру практически всё.'],
  [31,'avo',1,'Я проговариваю с партнёром то, что происходит.'],
  [32,'avo',0,'Я нервничаю, когда партнёр подходит слишком близко.'],
  [33,'avo',1,'Мне комфортно зависеть от партнёра.'],
  [34,'avo',1,'Мне легко опереться на партнёра.'],
  [35,'avo',1,'Мне легко проявлять нежность к партнёру.'],
  [36,'avo',1,'Партнёр по-настоящему понимает меня и мои потребности.']
];

const ORDER = (() => { const a=[],b=[],o=[];
  ITEMS.forEach(i => (i[1]==='anx'?a:b).push(i));
  for (let k=0;k<18;k++){ o.push(a[k]); o.push(b[k]); } return o; })();

const KEY='ecrr-state';
let answers={}, pos=0;
try { const s=JSON.parse(localStorage.getItem(KEY)||'{}');
      answers=s.a||{}; pos=Math.min(s.p||0,36); } catch(e){}

const save=()=>{ try{ localStorage.setItem(KEY,JSON.stringify({a:answers,p:pos})); }catch(e){} };

const $=id=>document.getElementById(id);

function draw(){
  if(pos>=36){ finish(); return; }
  const [n,,,text]=ORDER[pos];
  const cur=answers[n];
  $('quiz').innerHTML=`<div class="qi" id="qi${n}">
      <p class="qn">Вопрос ${pos+1} из 36</p>
      <p class="qt">${text}</p>
      <div class="scale"><span class="anc">Совсем не так</span>
        <div class="dots">${[1,2,3,4,5,6,7].map(v=>
          `<label class="opt${cur===v?' on':''}"><input type="radio" name="q" value="${v}"${cur===v?' checked':''}><span class="dot">${v}</span></label>`).join('')}</div>
        <span class="anc r">Именно так</span></div>
    </div>`;
  $('bar').style.width=(pos/36*100)+'%';
  $('pcount').textContent=`${pos} из 36`;
  $('next').textContent = pos===35 ? 'Показать результат' : 'Следующий';
  $('next').disabled = cur===undefined;
}

function pick(v){
  answers[ORDER[pos][0]]=v; save();
  document.querySelectorAll('#quiz .opt').forEach(l=>l.classList.toggle('on',+l.querySelector('input').value===v));
  $('next').disabled=false;
}

function finish(){
  const s=score();
  const t = s.anx<4 ? (s.avo<4?'sec':'dis') : (s.avo<4?'pre':'fea');
  const [name,desc]=TYPES[t];
  const tbl=sc=>s.rows[sc].map(r=>`<tr><td>${r.n}</td><td>${r.raw}</td><td>${r.rev?'да':'—'}</td><td>${r.val}</td></tr>`).join('');
  $('quiz').innerHTML=''; $('next').hidden=true;
  $('bar').style.width='100%'; $('pcount').textContent='36 из 36';
  $('res').innerHTML=`
    <h2 class="rt">${name}</h2>
    <p class="para">${desc}</p>
    <div class="gauge"><div class="gl"><span>Тревожность</span><b>${s.anx.toFixed(2)}</b><i>${band(s.anx)}</i></div>
      <div class="track"><div class="fill" style="width:${(s.anx-1)/6*100}%"></div><div class="mid"></div></div></div>
    <div class="gauge"><div class="gl"><span>Избегание</span><b>${s.avo.toFixed(2)}</b><i>${bandA(s.avo)}</i></div>
      <div class="track"><div class="fill" style="width:${(s.avo-1)/6*100}%"></div><div class="mid"></div></div></div>
    <p class="cnt">обе шкалы от 1 до 7 · тип определяется по середине, по четвёрке</p>
    <p class="para" style="font-size:14.5px;color:var(--muted)">Словесные пометки рядом с числами — только про выраженность: до 3 слабая, от 3 до 5 умеренная, выше 5 сильная. На тип они не влияют, и у границ не стоит читать их буквально: 5,06 и 4,94 отличаются на один балл в одном ответе.</p>
    <details class="node lvl2"><summary><span class="num">—</span><span class="t">Как это посчитано</span></summary>
      <div class="kids">
        <p class="para">Обратные пункты пересчитаны как <strong>8 минус ответ</strong>. По каждой шкале взято среднее из 18 значений.</p>
        <p class="para"><strong>Тревожность:</strong> сумма ${s.sumA} ÷ 18 = ${s.anx.toFixed(2)}<br>
        <strong>Избегание:</strong> сумма ${s.sumV} ÷ 18 = ${s.avo.toFixed(2)}</p>
        <div class="scroll"><table><thead><tr><th>Пункт</th><th>Ответ</th><th>Обратный</th><th>В зачёт</th></tr></thead>
        <tbody><tr class="hd"><td colspan="4">Тревожность, пункты 1–18</td></tr>${tbl('anx')}
        <tr class="hd"><td colspan="4">Избегание, пункты 19–36</td></tr>${tbl('avo')}</tbody></table></div>
      </div></details>`;
  $('res').hidden=false;
}

const recode=(n,rev,v)=>rev?8-v:v;

function score(){
  const rows={anx:[],avo:[]};
  ITEMS.forEach(([n,sc,rev])=>rows[sc].push({n,rev,raw:answers[n],val:recode(n,rev,answers[n])}));
  const mean=a=>a.reduce((s,r)=>s+r.val,0)/a.length;
  return {rows, anx:mean(rows.anx), avo:mean(rows.avo),
          sumA:rows.anx.reduce((s,r)=>s+r.val,0), sumV:rows.avo.reduce((s,r)=>s+r.val,0)};
}

const band  = v => v<3 ? 'слабая выраженность' : v<=5 ? 'умеренная' : 'сильная';
const bandA = v => v<3 ? 'слабая выраженность' : v<=5 ? 'умеренная' : 'сильная';

const TYPES={
  sec:['Надёжный','Обе шкалы ниже середины. Близость не вызывает напряжения, отсутствие ответа не читается как угроза. Опора на партнёра и своя самостоятельность уживаются друг с другом.'],
  pre:['Тревожный','Тревожность выше середины, избегание ниже. Близость желанна и переживается как ценность, при этом много внимания уходит на проверку: на месте ли чувства партнёра, не изменилось ли что-то.'],
  dis:['Избегающий','Избегание выше середины, тревожность ниже. Отвержение не пугает, напряжение возникает в другом месте — там, где нужно опереться на другого и допустить зависимость.'],
  fea:['Тревожно-избегающий','Обе шкалы выше середины. Близость одновременно нужна и опасна: сближение усиливает тревогу, а отдаление её не снимает.']
};

document.addEventListener('DOMContentLoaded',()=>{
  draw();
  $('quiz').addEventListener('change',e=>{ if(e.target.type==='radio') pick(+e.target.value); });
  $('next').addEventListener('click',()=>{ if(answers[ORDER[pos][0]]===undefined) return; pos++; save(); draw(); });
  document.addEventListener('keydown',e=>{
    if($('res').hidden===false) return;
    if(e.key>='1'&&e.key<='7'){ pick(+e.key); }
    else if(e.key==='Enter'&&!$('next').disabled){ $('next').click(); }
  });
  $('reset').addEventListener('click',()=>{
    answers={}; pos=0; save();
    $('res').hidden=true; $('next').hidden=false; draw();
    window.scrollTo({top:0,behavior:'smooth'});
  });
});
