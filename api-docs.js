// Illustrative examples. The UI supplies the current host so requests work on LAN or Tailscale.
const examples = [
  {group:'Network',title:'Check connection',method:'GET',path:'/api/status',response:{connected:true,ip:'192.168.1.42',ssid:'HomeWiFi',setup_ap:false},wire:'Power the Pico by USB; no external wiring is needed.'},
  {group:'Network',title:'Change the Wi-Fi network',method:'PUT',path:'/api/wifi',body:{ssid:'NewWiFi',password:'example-password'},response:{saved:true,rebooting:true},wire:'No external wiring. Reconnect using the Pico’s new DHCP address after reboot.'},
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
  {group:'I²C',title:'List I²C paths',method:'GET',path:'/api/i2c/buses',response:[{id:'direct:4',name:'Pico GP4 / GP5'},{id:'mux:6:0',name:'Sensor bus · Seed bay 1 (SD0 / SC0)'}],excerpt:true,wire:'Wire the mux upstream to GP4/GP5, then attach I²C devices to its SD/SC channel pairs.'},
  {group:'I²C',title:'Scan a mux channel',method:'POST',path:'/api/i2c/scan',body:{bus:'mux:6:0'},response:{addresses:[68]},wire:'An SHT30 at address 68 on mux SD0/SC0 will appear when channel 0 is scanned.'},
  {group:'I²C',title:'Read raw bytes',method:'POST',path:'/api/i2c/read',body:{bus:'mux:6:0',address:68,register:null,count:2},response:{address:68,register:null,data:[102,128],hex:'6680'},wire:'Use an I²C sensor on mux channel 0. Its datasheet determines whether to use a register and how to interpret bytes.'},
  {group:'I²C',title:'Write raw bytes',method:'POST',path:'/api/i2c/write',body:{bus:'mux:6:0',address:68,register:null,data:[36,0]},response:{address:68,register:null,written:2},wire:'For an SHT30 on channel 0, 24 00 hex starts a high-repeatability measurement. Read its result after the sensor’s delay.'},
];

const ledDiagram=[['Pico GP14 · pin 19','330 Ω resistor · orange-orange-brown-gold','LED anode (+) → cathode (−)','Pico GND · pin 18']];
const buttonDiagram=[['Pico GP12 · pin 16','push button','Pico GND · pin 18']];
const muxDiagram=[['Pico GP4 · pin 6','Mux SDA'],['Pico GP5 · pin 7','Mux SCL'],['Pico 3V3 · pin 36','Mux VCC'],['Pico GND · pin 8','Mux GND']];
const muxSensorDiagram=[...muxDiagram,['Mux SD0','SHT30 SDA'],['Mux SC0','SHT30 SCL'],['Pico 3V3 · pin 36','SHT30 VCC'],['Pico GND · pin 8','SHT30 GND']];
function diagramFor(example){
  if(/button/i.test(example.title))return buttonDiagram;
  if(/SHT30|sensor behind|mux channel|raw bytes/i.test(example.title))return muxSensorDiagram;
  if(/multiplexer|I²C paths/i.test(example.title))return muxDiagram;
  if(/LED|output pin|one GPIO|GPIO readings|pin note|Edit a device|List devices|Remove a device/i.test(example.title))return ledDiagram;
  return null;
}
function renderDiagram(paths){
  const figure=document.createElement('figure');figure.className='api-diagram';
  const caption=document.createElement('figcaption');caption.textContent='Wiring diagram · example physical pins';figure.append(caption);
  for(const path of paths){
    const row=document.createElement('div');row.className='api-wire-path';
    path.forEach((part,index)=>{if(index){const arrow=document.createElement('span');arrow.className='api-wire-arrow';arrow.textContent='→';row.append(arrow)}const label=document.createElement('span');label.className='api-wire-part';label.textContent=part;row.append(label)});
    figure.append(row);
  }
  return figure;
}

function renderApiExamples(){
  const box=document.querySelector('#api-docs'),query=document.querySelector('#api-search').value.toLowerCase().trim();
  box.replaceChildren();
  for(const example of examples){
    if(!`${example.group} ${example.title} ${example.method} ${example.path} ${example.wire}`.toLowerCase().includes(query))continue;
    const card=document.createElement('details');card.className='api-card';
    const summary=document.createElement('summary');summary.textContent=`${example.method} ${example.path} · ${example.title}`;card.append(summary);
    const note=document.createElement('p');note.textContent=example.wire;card.append(note);
    const diagram=diagramFor(example);if(diagram)card.append(renderDiagram(diagram));
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
