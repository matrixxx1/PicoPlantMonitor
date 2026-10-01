// Illustrative examples. The UI supplies the current host so requests work on LAN or Tailscale.
const examples = [
  {group:'Network',title:'Check connection',method:'GET',path:'/api/status',response:{connected:true,ip:'192.168.1.42',ssid:'HomeWiFi',setup_ap:false},wire:'Power the Pico by USB; no external wiring is needed.'},
  {group:'Network',title:'Change the Wi-Fi network',method:'PUT',path:'/api/wifi',body:{ssid:'NewWiFi',password:'example-password'},response:{saved:true,rebooting:true},wire:'No external wiring. Reconnect using the Pico’s new DHCP address after reboot.'},
  {group:'Network',title:'Restart the Pico',method:'POST',path:'/api/reboot',response:{rebooting:true},wire:'Power the Pico by USB. This restarts firmware without changing saved configuration; the web page briefly disconnects.'},
  {group:'Pins',title:'List GPIO readings',method:'GET',path:'/api/pins',response:[{pin:14,physical_pin:19,note:'Desk LED',configuration:{mode:'output',value:0},value:0,unit:null,devices:[]}],excerpt:true,wire:'Example shown for GP14; configure and wire each pin for the value you want to read.'},
  {group:'Pins',title:'Read one GPIO',method:'GET',path:'/api/pins/14',response:{pin:14,physical_pin:19,note:'Desk LED',configuration:{mode:'output',value:0},value:0,unit:null,devices:[]},wire:'An LED can use GP14 (physical 19) → 330 Ω → LED anode; LED cathode → GND.'},
  {group:'Pins',title:'Configure an output pin',method:'PUT',path:'/api/pins/14',body:{mode:'output',value:0,note:'Desk LED'},response:{saved:true,rebooting:true,pin:14},wire:'Wire GP14 → 330 Ω resistor → LED anode; LED cathode → a Pico GND pin. Save reboots the Pico.'},
  {group:'Pins',title:'Turn an output pin on',method:'PUT',path:'/api/pins/14/value',body:{value:1},response:{pin:14,physical_pin:19,note:'Desk LED',configuration:{mode:'output',value:0},value:1,unit:null,devices:[]},wire:'GP14 (physical 19) → 330 Ω resistor → LED anode; LED cathode → GND (physical 18). Send value 0 to turn it off.'},
  {group:'Pins',title:'Save a pin note',method:'PUT',path:'/api/pins/14/note',body:{note:'Desk LED'},response:{pin:14,physical_pin:19,note:'Desk LED',configuration:{mode:'output',value:0},value:0,unit:null,devices:[]},wire:'A note needs no wiring. It identifies the physical connection in the board view and API.'},
  {group:'Devices',title:'See supported device types',method:'GET',path:'/api/catalog',response:{button:{name:'Push button',category:'Buttons',description:'Reads pressed or released using an internal pull-up.',roles:[['SIGNAL','gpio'],['GND','ground']],wiring:'Connect the switch between SIGNAL and GND. Pressed reads 0.',resistor:null}},excerpt:true,wire:'No wiring is needed to browse the catalog; each type lists its required connections.'},
  {group:'Devices',title:'Create a push button',method:'POST',path:'/api/devices',body:{type:'button',name:'Start button',note:'Front panel',pins:{SIGNAL:16,GND:18}},response:{saved:true,rebooting:true,id:'4'},wire:'Connect a normally open button between GP12 (physical 16) and GND (physical 18). The Pico uses its internal pull-up.'},
  {group:'Devices',title:'Read a button',method:'GET',path:'/api/devices/4',response:{id:'4',type:'button',name:'Start button',note:'Front panel',pins:{SIGNAL:16,GND:18},address:null,reading:{pressed:true}},wire:'Connect a button between GP12 (physical 16) and GND (physical 18). Pressed returns true when the switch closes.'},
  {group:'Devices',title:'Create an LED device',method:'POST',path:'/api/devices',body:{type:'led',name:'Grow light indicator',note:'Seed tray',pins:{SIGNAL:19,GND:18}},response:{saved:true,rebooting:true,id:'5'},wire:'GP14 (physical 19) → 330 Ω resistor → LED anode; LED cathode → GND (physical 18).'},
  {group:'Devices',title:'Turn an LED device on',method:'PUT',path:'/api/devices/5/value',body:{value:1},response:{id:'5',type:'led',name:'Grow light indicator',note:'Seed tray',pins:{SIGNAL:19,GND:18},address:null,reading:{value:1}},wire:'GP14 (physical 19) → 330 Ω resistor → LED anode; LED cathode → GND (physical 18). Send value 0 to turn it off; no reboot is needed.'},
  {group:'Devices',title:'Edit a device',method:'PUT',path:'/api/devices/5',body:{type:'led',name:'Status LED',note:'Seed tray 2',pins:{SIGNAL:19,GND:18}},response:{saved:true,rebooting:true,id:'5'},wire:'Keep the LED and 330 Ω resistor on GP14 and GND, or update the physical pins to match the new wiring.'},
  {group:'Devices',title:'List devices',method:'GET',path:'/api/devices',response:[{id:'5',type:'led',name:'Status LED',note:'Seed tray 2',pins:{SIGNAL:19,GND:18},address:null,reading:{value:0}}],excerpt:true,wire:'The response reflects devices you have configured and physically wired.'},
  {group:'Devices',title:'Remove a device',method:'DELETE',path:'/api/devices/5',response:{deleted:true,rebooting:true},wire:'Disconnect the LED from GP14 after deleting its configuration, or reassign the pin to another device.'},
  {group:'Multiplexer',title:'Add an eight-channel multiplexer',method:'POST',path:'/api/devices',body:{type:'tca9548a',name:'Sensor bus',note:'Greenhouse',pins:{SDA:6,SCL:7,VCC:36,GND:8},address:112,channels:[{name:'Seed bay 1',note:''},{name:'Seed bay 2',note:''},{name:'',note:''},{name:'',note:''},{name:'',note:''},{name:'',note:''},{name:'',note:''},{name:'',note:''}]},response:{saved:true,rebooting:true,id:'6'},wire:'TCA9548A SDA → GP4 (physical 6), SCL → GP5 (7), VCC → 3V3 (36), GND → GND (8). A0–A2 low gives address 112.'},
  {group:'Multiplexer',title:'Add an SHT30 on channel 0',method:'POST',path:'/api/devices',body:{type:'sht30',name:'Bay 1 air',note:'Seed bay 1',pins:{SDA:6,SCL:7,VCC:36,GND:8},bus:'mux:6:0',address:68},response:{saved:true,rebooting:true,id:'7'},wire:'SHT30 SDA → mux SD0, SCL → mux SC0, VCC → Pico 3V3, GND → Pico GND. GP4/GP5 are the mux’s upstream pair.'},
  {group:'Multiplexer',title:'Read the sensor behind the mux',method:'GET',path:'/api/devices/7',response:{id:'7',type:'sht30',name:'Bay 1 air',note:'Seed bay 1',pins:{SDA:6,SCL:7,VCC:36,GND:8},address:68,bus:'mux:6:0',reading:{temperature_c:22.5,humidity_percent:48.1}},wire:'Pico GP4/GP5 → mux SDA/SCL; mux SD0/SC0 → SHT30 SDA/SCL. Power both boards from Pico 3V3 and GND.'},
  {group:'Devices',title:'Refresh one sensor now',method:'POST',path:'/api/devices/7/refresh',response:{id:'7',type:'sht30',name:'Bay 1 air',note:'Seed bay 1',pins:{SDA:6,SCL:7,VCC:36,GND:8},address:68,bus:'mux:6:0',reading:{temperature_c:22.6,humidity_percent:48.2}},wire:'Wire the SHT30 to mux SD0/SC0 and shared 3V3/GND as shown. This forces a new measurement for that sensor without rebooting; add 4.7 kΩ pull-ups only if the I²C boards lack them.'},
  {group:'Devices',title:'Enable SHT30 auto post',method:'PUT',path:'/api/devices/7',body:{type:'sht30',name:'Bay 1 air',note:'Seed bay 1',pins:{SDA:6,SCL:7,VCC:36,GND:8},address:68,bus:'mux:6:0',auto_post:{enabled:true,interval_minutes:60,url:'https://example.com/reading?temperature_c={temperature_c}&humidity_percent={humidity_percent}'}},response:{saved:true,rebooting:true,id:'7'},wire:'Wire SHT30 SDA/SCL to mux SD0/SC0, and its VCC/GND to Pico 3V3/GND. If the I²C boards lack pull-ups, add 4.7 kΩ from each SDA and SCL line to 3V3 on each bus segment. The Pico POSTs to /reading?temperature_c=22.5&humidity_percent=48.1 for a reading of 22.5 °C and 48.1% RH.'},
  {group:'I²C',title:'List I²C paths',method:'GET',path:'/api/i2c/buses',response:[{id:'direct:4',name:'Pico GP4 / GP5'},{id:'mux:6:0',name:'Sensor bus · Seed bay 1 (SD0 / SC0)'}],excerpt:true,wire:'Wire the mux upstream to GP4/GP5, then attach I²C devices to its SD/SC channel pairs.'},
  {group:'I²C',title:'Scan a mux channel',method:'POST',path:'/api/i2c/scan',body:{bus:'mux:6:0'},response:{addresses:[68]},wire:'An SHT30 at address 68 on mux SD0/SC0 will appear when channel 0 is scanned.'},
  {group:'I²C',title:'Read raw bytes',method:'POST',path:'/api/i2c/read',body:{bus:'mux:6:0',address:68,register:null,count:2},response:{address:68,register:null,data:[102,128],hex:'6680'},wire:'Use an I²C sensor on mux channel 0. Its datasheet determines whether to use a register and how to interpret bytes.'},
  {group:'I²C',title:'Write raw bytes',method:'POST',path:'/api/i2c/write',body:{bus:'mux:6:0',address:68,register:null,data:[36,0]},response:{address:68,register:null,written:2},wire:'For an SHT30 on channel 0, 24 00 hex starts a high-repeatability measurement. Read its result after the sensor’s delay.'},
];

function diagramFor(example){
  if(/button/i.test(example.title))return 'button';
  if(/SHT30|sensor behind|mux channel|raw bytes/i.test(example.title))return 'sensor';
  if(/multiplexer|I²C paths/i.test(example.title))return 'mux';
  if(/LED|output pin|one GPIO|GPIO readings|pin note|Edit a device|List devices|Remove a device/i.test(example.title))return 'led';
  return null;
}
const svgNS='http://www.w3.org/2000/svg';
function svgPart(parent,tag,attrs={},label){const item=document.createElementNS(svgNS,tag);for(const [key,value] of Object.entries(attrs))item.setAttribute(key,String(value));if(label!==undefined)item.textContent=label;parent.append(item);return item}
function renderDiagram(kind){
  const figure=document.createElement('figure');figure.className='api-diagram';
  const caption=document.createElement('figcaption');caption.textContent='Picture wiring guide · example physical pins';figure.append(caption);
  const svg=svgPart(figure,'svg',{viewBox:kind==='sensor'?'0 0 900 540':kind==='mux'?'0 0 760 475':'0 0 760 270','data-kind':kind,role:'img','aria-label':kind==='led'?'Pico GP14 through a 330 ohm resistor and LED to ground':kind==='button'?'Button between Pico GP12 and ground':'Pico I2C connections through a TCA9548A multiplexer'+(kind==='sensor'?' to an SHT30 sensor':'')});
  const rect=(x,y,w,h,fill='#fff',stroke='#337a50',rx=12)=>svgPart(svg,'rect',{x,y,width:w,height:h,fill,stroke,'stroke-width':3,rx});
  const wire=(points,color='#2d79b7',width=5)=>svgPart(svg,'polyline',{points,fill:'none',stroke:color,'stroke-width':width,'stroke-linecap':'round','stroke-linejoin':'round'});
  const text=(x,y,value,size=16,fill='#1b3c29',weight=500)=>svgPart(svg,'text',{x,y,fill,'font-size':size,'font-weight':weight},value);
  const dot=(x,y,color)=>svgPart(svg,'circle',{cx:x,cy:y,r:6,fill:color,stroke:'#fff','stroke-width':2});
  const board=(x,y,w,h)=>{rect(x,y,w,h,'#176b51','#0d503d',17);rect(x+w*.25,y-8,w*.5,18,'#dfe6e6','#9daaad',5);text(x+22,y+38,'PICO 2 W',20,'#fff',800)};
  const pullupInset=(x,y)=>{
    rect(x,y,360,94,'#fffaf0','#b9a377',9);text(x+12,y+20,'OPTIONAL · if board has no pull-ups',13,'#705826',800);
    wire(`${x+93},${y+36} ${x+302},${y+36}`,'#ce4c4c',3);text(x+12,y+42,'3V3',13,'#9d3a3a',800);
    for(const [left,label,color] of [[x+130,'SDA','#2d79b7'],[x+255,'SCL','#bb6e40']]){
      wire(`${left},${y+36} ${left},${y+48}`,color,3);rect(left-15,y+48,30,26,'#f4e2c4','#a9815d',4);
      for(const [offset,band] of [[-9,'#e9c432'],[-3,'#8d5ba6'],[3,'#c53535'],[9,'#d1a94e']])rect(left+offset,y+49,3,24,band,band,1);
      wire(`${left},${y+74} ${left},${y+84}`,color,3);text(left+20,y+69,'4.7 kΩ',11,'#5a3923',700);text(left-12,y+91,label,12,'#24483b',700);
    }
  };
  if(kind==='led'||kind==='button'){
    board(24,35,190,205);text(42,105,kind==='led'?'GP14 · pin 19':'GP12 · pin 16',15,'#fff',700);text(42,198,'GND · pin 18',15,'#fff',700);
    wire('214,100 290,100');wire('575,100 684,100 684,192 214,192','#263b43');dot(214,100,'#2d79b7');dot(214,192,'#263b43');
    if(kind==='led'){
      wire('400,100 510,100');rect(290,82,110,36,'#f4e2c4','#a9815d',9);
      for(const [x,color] of [[305,'#ed8b24'],[321,'#ed8b24'],[337,'#795136'],[375,'#d1a94e']])rect(x,83,11,34,color,color,2);
      text(306,70,'330 Ω resistor',15,'#5a3923',700);
      svgPart(svg,'circle',{cx:542,cy:100,r:32,fill:'#fff3ac',stroke:'#d69823','stroke-width':4});
      text(526,108,'LED',17,'#684717',800);text(505,60,'anode +',14);text(566,60,'cathode −',14);
      for(const [x1,y1,x2,y2] of [[512,67,499,51],[542,58,542,40],[572,68,585,51]])wire(`${x1},${y1} ${x2},${y2}`,'#efbe37',3);
      wire('574,100 575,100');text(267,226,'Orange · orange · brown · gold bands',13,'#65553e',600);
    }else{
      wire('290,100 350,100');wire('440,100 575,100');
      dot(350,100,'#2d79b7');dot(440,100,'#2d79b7');rect(368,59,54,20,'#add4ad','#377b48',5);wire('395,79 395,91','#377b48',4);wire('364,91 426,91','#377b48',4);
      text(338,53,'PUSH BUTTON',17,'#1c5934',800);text(320,226,'Uses Pico internal pull-up · no external resistor',13,'#48644e',600);
    }
    text(26,260,'Blue: signal     Dark: ground return',13,'#48644e',600);
  }else if(kind==='mux'){
    board(24,32,205,294);rect(442,32,275,294,'#e7f3e7','#34764e',16);text(468,73,'TCA9548A',22,'#174b2d',800);text(468,97,'I²C MULTIPLEXER',14,'#376448',700);
    for(const [y,left,right,color] of [[124,'GP4 · SDA · #6','SDA','#2d79b7'],[173,'GP5 · SCL · #7','SCL','#bb6e40'],[222,'3V3 · #36','VCC','#ce4c4c'],[271,'GND · #8','GND','#263b43']]){wire(`229,${y} 442,${y}`,color);dot(229,y,color);dot(442,y,color);text(42,y-8,left,14,'#fff',700);text(464,y+6,right,16)}
    text(470,310,'SD0/SC0 … SD7/SC7',15,'#376448',700);pullupInset(210,352);text(28,464,'Use a pull-up pair on each I²C segment only if the connected boards lack them.',13,'#48644e',600);
  }else{
    board(18,35,178,300);rect(348,35,205,300,'#e7f3e7','#34764e',15);rect(690,60,188,252,'#e7f0fa','#3579a4',15);
    text(365,76,'TCA9548A',21,'#174b2d',800);text(707,100,'SHT30',21,'#205575',800);
    for(const [y,left,mux,color] of [[124,'GP4 · SDA · #6','SDA','#2d79b7'],[170,'GP5 · SCL · #7','SCL','#bb6e40'],[232,'3V3 · #36','VCC','#ce4c4c'],[278,'GND · #8','GND','#263b43']]){wire(`196,${y} 348,${y}`,color);text(34,y-8,left,13,'#fff',700);text(363,y+6,mux,15);dot(348,y,color)}
    wire('553,124 690,124','#2d79b7');wire('553,170 690,170','#bb6e40');text(490,116,'SD0',14,'#376448',700);text(490,162,'SC0',14,'#376448',700);text(708,131,'SDA',15);text(708,177,'SCL',15);
    wire('196,232 272,232 272,348 640,348 640,224 690,224','#ce4c4c');wire('196,278 244,278 244,367 662,367 662,270 690,270','#263b43');text(707,231,'VCC',15);text(707,277,'GND',15);
    pullupInset(270,397);text(23,525,'If pull-ups are absent, use one pair on the Pico–mux segment and another on the mux–sensor segment.',13,'#48644e',600);
  }
  if(kind==='led'){const legend=document.createElement('p');legend.className='legend';legend.textContent='Resistor is in series with the LED. Its four bands are orange, orange, brown, gold.';figure.append(legend)}
  return figure;
}

function renderApiExamples(){
  const box=document.querySelector('#api-docs'),query=document.querySelector('#api-search').value.toLowerCase().trim();
  box.replaceChildren();
  for(const example of examples){
    if(!`${example.group} ${example.title} ${example.method} ${example.path} ${example.wire}`.toLowerCase().includes(query))continue;
    const card=document.createElement('details');card.className='api-card';
    const summary=document.createElement('summary');summary.textContent=`${example.method} ${example.path} · ${example.title}`;card.append(summary);
    const diagram=diagramFor(example),note=document.createElement('p');
    let wiring=example.wire;
    if(diagram==='led'&&!/330 Ω/.test(wiring))wiring+=' Use a 330 Ω series resistor between the Pico pin and LED anode.';
    if(diagram==='button'&&!/pull-up/i.test(wiring))wiring+=' The Pico uses its internal pull-up; no external resistor is needed.';
    if((diagram==='mux'||diagram==='sensor')&&!/pull-up/i.test(wiring))wiring+=' If the I²C boards lack pull-ups, use 4.7 kΩ from SDA and SCL to 3V3 on each bus segment.';
    note.textContent=wiring;card.append(note);
    if(diagram)card.append(renderDiagram(diagram));
    const grid=document.createElement('div');grid.className='api-grid';
    for(const [title,value] of [['Example request',`${example.method} ${location.origin}${example.path}${example.body?'\nContent-Type: application/json\n\n'+JSON.stringify(example.body,null,2):''}`],['Example response'+(example.excerpt?' (excerpt)':''),JSON.stringify(example.response,null,2)]]){
      const column=document.createElement('div'),heading=document.createElement('strong'),pre=document.createElement('pre');
      heading.textContent=title;pre.textContent=value;column.append(heading,pre);grid.append(column);
    }
    card.append(grid);box.append(card);
  }
  if(!box.children.length){const empty=document.createElement('p');empty.textContent='No matching endpoints.';box.append(empty)}
}
document.querySelector('#api-search').addEventListener('input',renderApiExamples);
renderApiExamples();
