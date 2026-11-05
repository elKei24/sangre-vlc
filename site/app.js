const map = L.map('map').setView([39.3, -0.5], 8);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);
const layer = L.layerGroup().addTo(map);
const from = document.getElementById('from');
const to = document.getElementById('to');
const fmt = new Intl.DateTimeFormat('es-ES', { weekday: 'short', day: 'numeric', month: 'short' });
const missingLink = document.getElementById('missing-link');
const missingDialog = document.getElementById('missing-dialog');
let places = [];

const isoDate = d => d.toISOString().slice(0, 10);
const plusDays = n => isoDate(new Date(Date.now() + n * 86400000));

function slotList(slots) {
  const byDay = {};
  for (const [d, h] of slots) (byDay[d] ??= []).push(h);
  return Object.keys(byDay).sort().map(d =>
    `<li><b>${fmt.format(new Date(d))}</b><span>${byDay[d].join(', ')}</span></li>`).join('');
}

function render() {
  layer.clearLayers();
  const missing = [];
  let n = 0;
  for (const p of places) {
    const slots = p.slots.filter(([d]) => (!from.value || d >= from.value) && (!to.value || d <= to.value));
    if (!slots.length) continue;
    n++;
    if (p.lat == null) {
      missing.push(`<li><b>${p.location}</b><span>${p.town} · ${slots.map(([d, h]) => `${fmt.format(new Date(d))} ${h}`).join(', ')}</span></li>`);
      continue;
    }
    const items = slotList(slots);
    L.circleMarker([p.lat, p.lon], {
      radius: 8, color: '#fff', weight: 2, fillColor: '#c8102e', fillOpacity: p.approx ? .45 : .95
    }).addTo(layer).bindPopup(
      `<div class="popup"><h3>${p.location}</h3><div class="town">${p.town} · ${p.province}</div>
       <ul>${items}</ul>${p.approx ? '<div class="approx">⚠ Dirección exacta no encontrada, marcador en el centro del municipio</div>' : ''}</div>`,
      { maxWidth: 320 });
  }
  document.getElementById('count').textContent = `${n} punto${n === 1 ? '' : 's'}`;
  missingLink.hidden = !missing.length;
  missingLink.textContent = `${missing.length} sin ubicación`;
  document.getElementById('missing').innerHTML = missing.join('');
  if (!missing.length) missingDialog.close();
}

function setRange(a, b) { from.value = a; to.value = b; render(); }
document.getElementById('today').onclick = () => setRange(plusDays(0), plusDays(0));
document.getElementById('week').onclick = () => setRange(plusDays(0), plusDays(6));
document.getElementById('all').onclick = () => setRange(plusDays(0), '');
from.oninput = to.oninput = render;

document.getElementById('info').onclick = () => document.getElementById('info-dialog').showModal();
missingLink.onclick = e => { e.preventDefault(); missingDialog.showModal(); };
for (const dialog of document.querySelectorAll('dialog')) {
  dialog.querySelector('.close').onclick = () => dialog.close();
  dialog.onclick = e => { if (e.target === dialog) dialog.close(); };
}
from.value = plusDays(0);

fetch('data.json').then(r => r.json()).then(d => {
  places = d.places;
  document.getElementById('updated').textContent = d.updated.slice(0, 16).replace('T', ' ');
  render();
});
