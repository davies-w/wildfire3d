// Execute generated chart code against a minimal DOM and check all legend toggles.
const fs=require('fs'),vm=require('vm'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'data/scenario_values/report.html'),'utf8');
const nodes=[],paths=[];
function make(tag){let text='';let x={tag,style:{},attrs:{},append(){},setAttribute(k,v){this.attrs[k]=v},get innerHTML(){return text},set innerHTML(v){text=v;if(tag==='svg'){for(const m of v.matchAll(/<path data-series="(\d)"/g))paths.push({dataset:{series:m[1]},style:{}})}}};nodes.push(x);return x}
const buttons=Array.from({length:4},(_,k)=>({dataset:{series:String(k)},attrs:{},setAttribute(k,v){this.attrs[k]=v},addEventListener(event,fn){this.click=fn}}));
const document={createElement:make,createElementNS:(_,t)=>make(t),getElementById:()=>make('root'),querySelectorAll(selector){if(selector==='.legend button')return buttons;let k=selector.match(/data-series="(\d)"/)[1];return paths.filter(x=>x.dataset.series===k)}};
vm.runInNewContext(source.split('<script>')[1].split('</script>')[0],{document});
if(nodes.filter(x=>x.tag==='svg').length!==4||paths.length!==16)throw Error('Incomplete rendering');
for(let k=0;k<4;k++){buttons[k].click();if(paths.filter(x=>x.style.display==='none').length!==4)throw Error('Incorrect hide');buttons[k].click();if(paths.some(x=>x.style.display==='none'))throw Error('Incorrect show');}
console.log('PASS: four panels; each legend toggles exactly four curves, then restores them.');
