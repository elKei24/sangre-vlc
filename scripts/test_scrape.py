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
assert list(scrape.queries("LA POBLA-CENTRO SOCIAL, C/SENYERA 31")) == ["C/SENYERA 31", "CENTRO SOCIAL", "C/SENYERA"]
assert list(scrape.queries("VALENCIA - AUTORIDAD PORTUARIA (SOLO EMPLEADOS) ANTESALA SALÓN DE ACTOS (PLANTA BAJA), AVDA MUELLE DEL TURIA S/N - FASE III")) == [
    "AVDA MUELLE DEL TURIA", "AUTORIDAD PORTUARIA"]
assert scrape.street("AGOST-CENTRO SOCIAL, GIMNASIO, AVDA. CONSELL PAIS VALENCIÀ, 16-18") == "AVDA. CONSELL PAIS VALENCIÀ, 16-18"
assert scrape.venue("ALICANTE-C.S.LOS ÁNGELES, GIMNASIO MATRONA, C/ LINARES, 9") == "CENTRO DE SALUD LOS ÁNGELES"
assert scrape.venue("ALCOI-CIP FP BATOI SALÓN DE ACTOS, C/ SOCIEDAD UNIÓN MUSICAL, 8") == "CIP FP BATOI"
assert scrape.venue("ALTEA - CIM, SALA 2, C/ MARINA BAIXA, 6") == "CIM"
assert scrape.street("BIAR-CASA DE CULTURA, PLANTA BAJA, PLAZA DEL CONVENTO") == "PLAZA DEL CONVENTO"
assert scrape.town_name("ALMASSORA/ALMAZORA") == "ALMASSORA"
assert scrape.town_name("ALCUDIA, L'") == "L'ALCUDIA"
assert scrape.town_name("VILA JOIOSA (LA)") == "LA VILA JOIOSA"
print("ok")
