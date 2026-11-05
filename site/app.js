const map = new maplibregl.Map({
  container: 'map',
  style: 'https://tiles.openfreemap.org/styles/liberty',
  bounds: [[-1.6, 37.8], [0.6, 40.85]],
  fitBoundsOptions: { padding: 16 },
  maxZoom: 18
});
map.addControl(new maplibregl.NavigationControl({ showCompass: false }));
const geojson = { type: 'FeatureCollection', features: [] };

// Pans the map so that an element, for example a popup, is fully visible.
function panIntoView(el, pad = 12) {
  const r = el.getBoundingClientRect(), m = map.getContainer().getBoundingClientRect();
  const dx = r.left < m.left + pad ? r.left - m.left - pad : Math.max(0, r.right - m.right + pad);
  const dy = r.top < m.top + pad ? r.top - m.top - pad : Math.max(0, r.bottom - m.bottom + pad);
  if (dx || dy) map.panBy([dx, dy]);
}
map.on('load', () => {
  map.addSource('places', { type: 'geojson', data: geojson });
  map.addLayer({
    id: 'places', type: 'circle', source: 'places',
    paint: {
      'circle-radius': 8, 'circle-color': '#c8102e',
      'circle-opacity': ['case', ['get', 'approx'], .45, .95],
      'circle-stroke-color': '#fff', 'circle-stroke-width': 2
    }
  });
  map.on('click', 'places', e => {
    const f = e.features[0];
    const popup = new maplibregl.Popup({ maxWidth: 'min(320px, 100vw - 48px)', offset: 10 })
      .setLngLat(f.geometry.coordinates).setHTML(f.properties.html).addTo(map);
    // The popup is positioned a frame after it is added.
    requestAnimationFrame(() => requestAnimationFrame(() => panIntoView(popup.getElement())));
  });
  map.on('mouseenter', 'places', () => { map.getCanvas().style.cursor = 'pointer'; });
  map.on('mouseleave', 'places', () => { map.getCanvas().style.cursor = ''; });
});
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
  geojson.features = [];
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
    const html = `<div class="popup"><h3>${p.location}</h3><div class="town">${p.town} · ${p.province}</div>
       <ul>${slotList(slots)}</ul>${p.approx ? '<div class="approx">⚠ Dirección exacta no encontrada, marcador en el centro del municipio</div>' : ''}</div>`;
    geojson.features.push({
      type: 'Feature', geometry: { type: 'Point', coordinates: [p.lon, p.lat] },
      properties: { html, approx: !!p.approx }
    });
  }
  map.getSource('places')?.setData(geojson);
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
