# job-radar

**Un radar diario de ofertas remotas, rankeadas contra mi perfil real.** No postula solo: rankea,
explica cada punto y escribe el borrador del mensaje. Apretar enviar lo hago yo.

Corre todos los días en GitHub Actions y publica el tablero en
**[lucabaello1998.github.io/job-radar](https://lucabaello1998.github.io/job-radar/)**.

## El problema

Buscar trabajo a mano tiene dos costos escondidos: revisar decenas de portales que repiten las
mismas ofertas, y escribir el mismo mensaje veinte veces. Lo aburrido se automatiza; lo que
requiere criterio — decidir si vale la pena y cómo contarse — no.

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
| híbrido / presencial | −2 / −3 |
| "US only", permiso de trabajo en EE.UU., clearance | −5 |
| pide 10+ años, principal, staff | −3 |
| pasantía, sin pago | −5 / −8 |

Con menos de 6 puntos no se publica. El tope es 100 y el tablero marca "encaje alto" desde 60.

## Correrlo

```bash
python -m jobradar.construir                # corrida completa (sale a la red)
python -m jobradar.construir --offline      # contra los fixtures, sin red
python -m jobradar.construir --solo remoteok
python -m jobradar.construir --docs /tmp/x  # a otra carpeta
python -m pytest                            # 20 tests
```

Solo biblioteca estándar de Python 3.11+. Sin requests, sin pandas, sin node_modules.

## El registro de postulaciones

El tablero no es un CRM: es la lista corta. El seguimiento vive en `postulaciones.jsonl`, que es
la única fuente de verdad del funnel.

```bash
python -m jobradar.estado add remoteok:1130000 aplicada --empresa "Acme" --titulo "Fullstack"
python -m jobradar.estado add remoteok:1130000 entrevista --nota "hablé con el gerente"
python -m jobradar.estado resumen
```

Estados: `por_postular`, `aplicada`, `respondida`, `entrevista`, `tecnica`, `oferta`, `descartada`.
Cada línea es un evento, así que el histórico queda completo y el tablero muestra el último estado.

## Por qué no postula solo

LinkedIn y Computrabajo prohíben los bots y tienen captcha. Más importante: una postulación
automática y genérica se nota, y quema la oportunidad. El radar hace el 90% aburrido — encontrar,
filtrar, rankear, escribir el borrador — y deja el 10% que importa en manos de una persona.

## Límites

- El puntaje es una heurística de palabras clave. Ordena la lista, no decide por mí.
- Las fuentes no cubren todo el mercado argentino: para ofertas locales conviene mirar además
  Computrabajo y LinkedIn a mano.
- Los salarios vienen tal cual los publica cada portal, en su moneda. No se convierten ni se estiman.

## Licencia

MIT.
