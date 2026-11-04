import datetime as dt
import scrape

PAGE = """<p class="subtitulo2">Viernes, 2 de enero</p><table>
<tr><td class="textotabla2sincursor poblacion"><b class="d-lg-none">Población: </b>POBLA DE VALLBONA, LA
</td><td class="textotabla2sincursor ubicacion"><b class="d-lg-none">Ubicación: </b>LA POBLA-CENTRO SOCIAL, C/SENYERA 31
</td><td class="textotabla2sincursor horario"><b class="d-lg-none">Horario: </b>17:00-20:30
</td></tr>
<tr><td class="textotabla2sincursor poblacion"><b class="d-lg-none">Población: </b>BARXETA
</td><td class="textotabla2sincursor ubicacion"><b class="d-lg-none">Ubicación: </b>SUSPENDIDO - BARXETA
</td><td class="textotabla2sincursor horario"><b class="d-lg-none">Horario: </b>-
</td></tr></table>"""

rows = list(scrape.parse(PAGE, dt.date(2026, 11, 4)))
assert rows == [(dt.date(2027, 1, 2), "POBLA DE VALLBONA, LA", "LA POBLA-CENTRO SOCIAL, C/SENYERA 31", "17:00-20:30")], rows
assert list(scrape.queries("POBLA DE VALLBONA, LA", "LA POBLA-CENTRO SOCIAL, C/SENYERA 31", "Valencia")) == [
    "C/SENYERA 31, LA POBLA DE VALLBONA, Valencia",
    "C/SENYERA, LA POBLA DE VALLBONA, Valencia",
    "LA POBLA DE VALLBONA, Valencia"]
assert scrape.town_name("ALMASSORA/ALMAZORA") == "ALMASSORA"
assert scrape.town_name("ALCUDIA, L'") == "L'ALCUDIA"
print("ok")
