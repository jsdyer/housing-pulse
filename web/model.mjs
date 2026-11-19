export function unpack(v) {return Array.isArray(v)?v:[v??null,''];}
export function period(key,frequency) {
  if(frequency!=='Quarterly')return key;
  return key.slice(0,4)+' Q'+(Math.floor((Number(key.slice(5))-1)/3)+1);
}
export function datesFor(from,to,frequency){
  const dates=[];let year=Number(from.slice(0,4)),month=frequency==='Annual'?1:Number(from.slice(5));
  while(year<=Number(to.slice(0,4))){
    const key=frequency==='Annual'?String(year):year+'-'+String(month).padStart(2,'0');
    if(key>to)break;dates.push(key);
    month+=frequency==='Annual'?12:frequency==='Monthly'?1:3;
    if(month>12){month-=12;year++;}
  }
  return dates;
}
