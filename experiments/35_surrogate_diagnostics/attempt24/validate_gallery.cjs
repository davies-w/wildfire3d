// Execute gallery rendering and pagination locally without network or browser access.
const fs=require('fs'),path=require('path'),vm=require('vm'),root=path.join(__dirname,'data/scenario_gallery');
const html=fs.readFileSync(path.join(root,'report.html'),'utf8');let context,ids={};
function element(tag){return {tag,innerHTML:'',textContent:'',style:{},children:[],append(n){this.children.push(n);if(n.tag==='script')vm.runInContext(fs.readFileSync(path.join(root,n.src),'utf8'),context)},setAttribute(){}}}
for(const id of ['rows','back','next','count'])ids[id]=element('div');const buttons=Array.from({length:4},(_,i)=>({...element('button'),dataset:{series:String(i)}}));
const document={getElementById:id=>ids[id],createElement:element,head:element('head'),querySelectorAll:s=>s==='#legend button'?buttons:[]};context=vm.createContext({document,window:{},location:{hash:''},history:{replaceState(){}},console});context.window=context;
vm.runInContext(html.split('<script>')[1].split('</script>')[0],context);
let seen=[];
for(let p=0;p<174;p++){
 vm.runInContext(`load(${p});`,context);const records=vm.runInContext(`cache[${p}]`,context);seen.push(...records.map(x=>x.index));let rows=ids.rows.children.slice(-records.length);for(const r of rows){if((r.innerHTML.match(/class="chart"/g)||[]).length!==4||(r.innerHTML.match(/<path data-series=/g)||[]).length!==16)throw Error('Missing chart or series')}
}
if(seen.length!==520||new Set(seen).size!==520)throw Error('Missing/duplicate history');vm.runInContext('load(0)',context);if(!ids.back.disabled)throw Error('Back boundary');vm.runInContext('load(173)',context);if(!ids.next.disabled)throw Error('Next boundary');
console.log('PASS: 174 pages, 520 unique histories, four charts and16 forecast curves per scenario; page boundaries work.');
