import {el,node,edition,choices,cards,table,chart,pretty,fail} from './ui.mjs';
import {unpack,period,datesFor} from './model.mjs';
let data,status;
const selected=id=>el(id).value;
function keepMarket(places,old,fallback) {
  if(places.includes(old))return old;
  return places.find(p=>p.split(',')[0]===(old||fallback).split(',')[0])||places.find(p=>p.startsWith(fallback))||places[0];
}
function setKinds(){
  const kinds=Object.keys(data.series[selected('metric')]).sort(),old=selected('kind');
  choices('kind',kinds,kinds.includes(old)?old:(kinds.find(k=>k==='Apartment - 2 bedrooms')||kinds.find(k=>k==='Rental · Total units')||kinds.find(k=>k==='Total units')));
  setPlaces();
}
function setPlaces(){
  const places=Object.keys(data.series[selected('metric')][selected('kind')]).sort();
  for(const [id,fallback] of [['left','Halifax'],['right','Vancouver']])choices(id,places,keepMarket(places,selected(id),fallback));
  setPeriods();
}
function setPeriods(){
  const series=data.series[selected('metric')][selected('kind')],a=series[selected('left')],b=series[selected('right')],freq=data.metrics[selected('metric')].frequency;
  const keys=[...new Set([...Object.keys(a),...Object.keys(b)])].sort();
  const all=datesFor(keys[0],keys.at(-1),freq),old=selected('period');
  choices('period',[...all].reverse().map(d=>[d,period(d,freq)]),all.includes(old)?old:all.at(-1));render();
}
function render(){
  const metric=selected('metric'),kind=selected('kind'),a=selected('left'),b=selected('right'),when=selected('period'),info=data.metrics[metric],series=data.series[metric][kind];
  const read=(geo,t)=>unpack(series[geo]?.[t]);
  function fmt(geo,t){const [v,flag]=read(geo,t);return pretty(v,info.unit)+(flag?' ['+flag+']':'');}
  cards([[a,fmt(a,when),period(when,info.frequency)],[b,fmt(b,when),period(when,info.frequency)]]);
  const av=read(a,when)[0],bv=read(b,when)[0];
  el('summary').textContent=av==null||bv==null?'At least one market has no published value for this reference period.':b+' minus '+a+' gives '+pretty(bv-av,info.unit==='%'?'percentage points':info.unit)+'.';
  el('method').textContent=info.frequency+' observations. '+info.note;
  const months=[...el('period').options].map(o=>o.value).reverse().filter(t=>t<=when);
  const view=selected('window')==='all'?months:months.slice(-Number(selected('window')));
  chart(view.map(t=>period(t,info.frequency)),[view.map(t=>read(a,t)[0]),view.map(t=>read(b,t)[0])],[a,b]);
  table('table',['Period',a,b],[...view].reverse().map(t=>[period(t,info.frequency),fmt(a,t),fmt(b,t)]));
  const source='https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid='+info.table+'01';el('tablelink').href=source;
  el('credit').textContent=info.table==='46100092'?'Source: Statistics Canada, Quarterly rent statistics, table 46-10-0092-01. E indicates a value to use with caution; F indicates a value too unreliable to publish.':'Adapted from Canada Mortgage and Housing Corporation, '+info.note.split('.')[0]+', '+period(when,info.frequency)+'. This does not constitute an endorsement by Canada Mortgage and Housing Corporation of this product.';
}
async function start(){
  [data,status]=await edition();
  el('status').textContent=status.count.toLocaleString('en-CA')+' published observations · Construction history '+status.start+' to '+status.end+' · Retrieved '+status.retrieved;
  choices('metric',Object.keys(data.metrics),'Average asking rent');el('metric').onchange=setKinds;el('kind').onchange=setPlaces;
  el('left').onchange=el('right').onchange=setPeriods;el('period').onchange=el('window').onchange=render;
  el('content').hidden=false;setKinds();
}
start().catch(fail);
