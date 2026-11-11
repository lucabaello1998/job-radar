# job-radar

**Un radar diario de ofertas remotas, rankeadas contra mi perfil real.** No postula solo: rankea,
explica cada punto y escribe el borrador del mensaje. Apretar enviar lo hago yo.

Corre todos los días en GitHub Actions y publica el tablero en
**[lucabaello1998.github.io/job-radar](https://lucabaello1998.github.io/job-radar/)**.

## Empezá acá

| Quiero… | Ir a |
|---|---|
| Ver las ofertas de hoy | [el tablero publicado](https://lucabaello1998.github.io/job-radar/) |
| Correrlo en mi máquina sin tocar la red | `python -m jobradar.construir --offline` |
| Volver a correrlo ahora mismo en la nube | Actions → *Radar* → *Run workflow* |
| Anotar que ya me postulé | `python -m jobradar.estado add <id> aplicada` |
| Cambiar qué ofertas me interesan | editar `jobradar/puntuar.py` |

## El problema

Buscar trabajo a mano tiene dos costos escondidos: revisar decenas de portales que repiten las
mismas ofertas, y escribir el mismo mensaje veinte veces. Lo aburrido se automatiza; lo que
requiere criterio - decidir si vale la pena y cómo contarse - no.

## Cómo funciona

```
fuentes API  →  deduplicar  →  puntuar  →  tablero + registro
```

| Etapa | Qué hace |
|---|---|
| **Recolecta** | Remotive, RemoteOK y GetOnBoard. Todas APIs públicas, sin login ni scraping |
| **Deduplica** | Empresa + título normalizados: la misma oferta en dos portales entra una vez |
| **Filtra** | Descarta lo que no es un rol de desarrollo (títulos de ventas, soporte, diseño) |
| **Puntúa** | Reglas explícitas, cada punto con su motivo visible en la tarjeta |
| **Publica** | Un HTML autocontenido, sin build ni CDN, que abre offline |

Si una fuente se cae, la corrida sigue y el tablero lo informa. Ninguna API tiene la culpa de que
el radar no funcione.

## El puntaje

No es una caja negra. Cada tarjeta muestra los motivos:

| Señal | Puntos |
|---|---|
| `.NET` / `C#` / `ASP.NET` | +4 |
| `React` o `Next.js` | +3 |
| `fullstack` | +3 |
| `TypeScript` | +2 |
| remoto / worldwide / anywhere | +2 |
| Argentina / LatAm / South America | +2 |
| paga en USD | +2 |
| híbrido / presencial | -2 / -3 |
| "US only", permiso de trabajo en EE.UU., clearance | -5 |
| pide 10+ años, principal, staff | -3 |
| pasantía, sin pago | -5 / -8 |

Con menos de 6 puntos no se publica. El tope es 100 y el tablero marca "encaje alto" desde 60.

## Instalación

No hay dependencias: es biblioteca estándar de Python 3.11+.

```bash
git clone https://github.com/lucabaello1998/job-radar.git
cd job-radar
python -m venv .venv
.venv\Scripts\activate          # Windows; en Linux/macOS: source .venv/bin/activate
pip install pytest ruff         # sólo para correr los tests y el lint
```

## Correrlo

```bash
python -m jobradar.construir                # corrida completa (sale a la red)
python -m jobradar.construir --offline      # contra los fixtures, sin red (escribe docs-preview/)
python -m jobradar.construir --solo remoteok
python -m jobradar.construir --docs /tmp/x  # a otra carpeta
python -m jobradar.construir --minimo 40    # subir el corte de publicación
python -m pytest                            # 22 tests
ruff check jobradar tests && ruff format --check jobradar tests
```

Una corrida `--offline` **no pisa el tablero publicado**: escribe en `docs-preview/`, que está
ignorado por git. Sirve para ver cómo queda un cambio de reglas sin tocar lo que está online.

Los fixtures de `fixtures/` son respuestas reales de las tres APIs. `--guardar-fixtures` las
actualiza: sirve cuando un portal cambia el formato y querés ver el JSON crudo.

## Cómo leer el tablero

1. **Encaje alto (60+)** es la lista corta del día. El resto está para husmear, no para postularse.
2. Cada tarjeta muestra **por qué** sumó: los chips de motivos salen de las mismas reglas del puntaje.
3. **Copiar mensaje** arma el borrador en español o inglés según el idioma del aviso. Se pega en el
   portal y se ajusta a mano: dos líneas específicas de la empresa valen más que el template entero.
4. **Ver oferta** abre el aviso original. Si el link está roto, el portal lo cerró: descartala.
5. El puntaje ordena, no decide. Si una oferta te gusta y está en 35, postulate igual.

## Despliegue

Ya está armado y no necesita secretos ni tokens:

- **GitHub Actions** (`.github/workflows/radar.yml`) corre todos los días a las 08:00 de Buenos Aires
  (11:00 UTC) y también a mano desde la pestaña *Actions*.
- El workflow corre tests, lint y formato antes de generar el tablero: si algo falla, no publica.
- **GitHub Pages** sirve la carpeta `docs/` de la rama `main`
  (*Settings → Pages → Source: Deploy from a branch → main / docs*).
- Si la corrida no trae cambios, no commitea nada: el historial no se llena de ruido.

Para publicarlo en tu propio fork:

1. Hacé fork y activá Pages con la carpeta `docs/`.
2. En *Actions*, habilitá los workflows si GitHub los pide.
3. Ajustá `AGENTE` en `jobradar/fuentes.py` con tu contacto (es cortesía con las APIs públicas).
4. Cambiá el perfil en `jobradar/puntuar.py` y el texto del mensaje en `jobradar/tablero.py`.

## El registro de postulaciones

El tablero no es un CRM: es la lista corta. El seguimiento vive en `postulaciones.jsonl`, que es
la única fuente de verdad del funnel.

```bash
python -m jobradar.estado add remoteok:1130000 aplicada --empresa "Acme" --titulo "Fullstack"
python -m jobradar.estado add remoteok:1130000 entrevista --nota "hablé con el gerente"
python -m jobradar.estado list
python -m jobradar.estado resumen
```

Estados: `por_postular`, `aplicada`, `respondida`, `entrevista`, `tecnica`, `oferta`, `descartada`.
Cada línea es un evento, así que el histórico queda completo y el tablero muestra el último estado.

`postulaciones.jsonl` **se commitea**: el radar corre en la nube y sólo puede pintar estados si el
archivo está en el repo. Es un archivo de texto, no tiene datos sensibles más allá de dónde te
postulaste.

## Estructura

```
jobradar/
  fuentes.py    clientes de las tres APIs + fixtures
  modelo.py     Oferta, limpieza de HTML, slug de deduplicación
  puntuar.py    reglas del perfil: qué suma, qué resta, qué no es un rol tech
  construir.py  la corrida: recolectar → procesar → escribir tablero y JSON
  tablero.py    HTML autocontenido (CSS y JS embebidos, sin CDN)
  estado.py     CLI del registro de postulaciones
fixtures/       respuestas crudas de las APIs para correr offline
docs/           lo que publica Pages: index.html y data/ofertas.json
tests/          pytest de reglas, deduplicación, fechas y estados
```

## Límites

- El puntaje es una heurística de palabras clave. Ordena la lista, no decide por mí.
- Las fuentes no cubren todo el mercado argentino: para ofertas locales conviene mirar además
  Computrabajo y LinkedIn a mano.
- Los salarios vienen tal cual los publica cada portal, en su moneda. No se convierten ni se estiman.
- GetOnBoard publica en varios países de LatAm: la ubicación se muestra tal cual, sin traducir.

## Si algo no anda

| Síntoma | Qué mirar |
|---|---|
| "sin ofertas publicables" | es normal en finde o feriado: las APIs publican menos. Probá `--minimo 0` para ver todo |
| Una fuente caída todos los días | `python -m jobradar.construir --solo <fuente>` y mirá el error; si la API cambió, actualizá el parser de `fuentes.py` |
| El tablero no se actualiza en Pages | Actions → última corrida → paso "Publicar si hubo cambios"; y que Pages apunte a `docs/` |
| Los tests fallan después de cambiar reglas | `pytest -q` muestra el punto exacto; los fixtures no cambian, así que la diferencia es tu cambio |

## Por qué no postula solo

LinkedIn y Computrabajo prohíben los bots y tienen captcha. Más importante: una postulación
automática y genérica se nota, y quema la oportunidad. El radar hace el 90% aburrido - encontrar,
filtrar, rankear, escribir el borrador - y deja el 10% que importa en manos de una persona.

## Licencia

MIT.
