# Manual: Reloj del Apocalipsis · índice diario

Estimación **no oficial**. El reloj real lo fija una vez al año el Science and Security Board del Bulletin of the Atomic Scientists (85 s en enero de 2026). Este proyecto mide la presión diaria de las noticias frente a esa línea base. Nunca lo presentes como el reloj oficial.

## 1. Cómo funciona (flujo diario)

```
  RSS de medios ──► spider.py ──► IA (OpenRouter) ──► data.json ──► index.html
  (CNN, NYT, BBC,   1) filtra     3) riesgo -5..+5   titulares +   dibuja reloj,
   RT, Fórmula,      por palabras  confiabilidad      historial     factores,
   Reddit…)          clave         señales, motivo    diario        anuncios,
                     2) mide                                        3 historiales
                     replicación
```

1. **Descarga:** el spider lee los RSS de cada medio (una vez al día) y se queda con los titulares que tocan algún factor (nuclear, clima, biológico, IA, geopolítica). Tope: 120 al día.
2. **Replicación:** compara titulares entre medios y cuenta cuántos medios confiables y cuántas fuentes extraoficiales repiten cada noticia.
3. **IA:** una sola llamada a la API de OpenRouter devuelve, por titular, factor, riesgo (−5 a +5), confiabilidad, señales (sensacionalista, estatal, sin_corroborar…) y una justificación breve.
4. **Confiabilidad final** = 35 % fiabilidad previa de la fuente + 40 % juicio de la IA + 25 % replicación.
5. **Índice:** cada titular aporta `riesgo/5 × confiabilidad × decaimiento (vida media 20 días) × 3` a su factor (tope ±15 por factor). Luego `R = 0.40N + 0.25C + 0.15B + 0.10I + 0.10G` y `segundos = 85 × (100−R)/(100−R₀)`.
6. **Respaldo:** sin clave de API, o si la IA falla, se usan las listas de palabras clave.
7. **Salida:** `data.json` = últimos 45 días de titulares evaluados + historial diario de segundos. La página lo lee y calcula lo mismo en el navegador.

La página muestra: reloj, factores, anuncios/conclusiones, tabla de medios, historial (cada 5 años oficial, último año, último mes), titulares con su evaluación y el apartado de donativos/publicidad.

## 2. Qué opción de montaje elegir

| | A. GitHub Actions + Pages (recomendada) | B. PythonAnywhere + hosting estático | C. Raspberry Pi |
|---|---|---|---|
| Costo | $0 (+ API de OpenRouter) | $0 si tu cuenta lo permite (+ API) | Hardware + electricidad (+ API) |
| Servidores a mantener | Ninguno | Uno (Flask) + el hosting estático | Tu propia Pi |
| Riesgo principal | Programas pueden pausarse por inactividad | Lista blanca de internet y CPU de la cuenta gratuita | Cortes de luz/red, seguridad si la expones |
| Dificultad | Baja | Media | Media |

**Mi recomendación: A.** No tiene la lista blanca de PythonAnywhere, guarda la clave como secreto y la página y los datos viven en el mismo sitio (sin CORS). Usa B solo si ya tienes cuenta; usa C si quieres control total o ya tienes la Pi encendida.

Verifica los límites vigentes en la documentación de cada servicio: cambian y las fuentes que consulté se contradicen en algunos detalles de la cuenta gratuita de PythonAnywhere (tarea programada diaria sí/no).

## 3. Requisito común: clave de OpenRouter

1. Crea cuenta en openrouter.ai y agrega crédito.
2. Crea una clave dedicada a este proyecto (Settings → Keys) y ponle un **límite de crédito** bajo.
3. Guárdala solo como secreto/variable de entorno, **nunca** en `index.html` ni en el repositorio.
4. Modelo: variable `OPENROUTER_MODEL` (por defecto `openai/gpt-4o-mini`). Copia el slug exacto de openrouter.ai/models; un modelo barato basta para empezar y uno más capaz da mejor criterio. El spider espera que el modelo devuelva una lista JSON; si responde otra cosa, usa el respaldo por palabras clave.

## 4. Opción A: GitHub Actions + GitHub Pages

1. Crea un repositorio en GitHub y sube **todo el contenido de esta carpeta** (incluida `.github/`).
2. Settings → Secrets and variables → Actions → *New repository secret*: nombre `OPENROUTER_API_KEY`, valor tu clave. (Opcional: pestaña *Variables* → *New repository variable* `OPENROUTER_MODEL` con el slug del modelo; si no la creas, se usa `openai/gpt-4o-mini`.)
3. Settings → Pages → *Deploy from a branch* → rama `main`, carpeta `/docs`.
4. Pestaña Actions → *reloj-diario* → *Run workflow* para la primera corrida. Debe aparecer un commit `datos AAAA-MM-DD` con `docs/data.json`.
5. Tu página: `https://TU_USUARIO.github.io/NOMBRE_REPO/`.
6. El flujo corre cada día a las 12:00 UTC (06:00 CDMX). Cambia la hora en el `cron` del YAML.

Notas: en repositorios públicos GitHub puede desactivar flujos programados tras ~60 días sin actividad; revisa que siga activo (ver mantenimiento). Si el repositorio es público, `data.json` también lo es (solo contiene titulares, enlaces y evaluaciones).

## 5. Opción B: PythonAnywhere (spider) + hosting estático (página)

**Spider y API de datos**
1. Cuenta en pythonanywhere.com. Consola Bash: `pip install --user feedparser`.
2. Sube `spider.py` y `app.py`. En ambos reemplaza `USUARIO` por tu usuario (o define `DATA_PATH`).
3. Pestaña Tasks: tarea diaria con el comando  
   `OPENROUTER_API_KEY=sk-or-... python3 /home/USUARIO/spider.py`
4. Pestaña Web → *Add a new web app* → Flask → apunta el WSGI a `app.py`. Tu JSON quedará en `https://USUARIO.pythonanywhere.com/data.json` (con CORS abierto).
5. **Lista blanca:** en cuentas gratuitas solo se puede salir a sitios permitidos. Prueba en consola que cada RSS y `openrouter.ai` respondan. Los que fallen se omiten, pero sin `openrouter.ai` no habrá análisis por IA (funcionará el respaldo por palabras clave). Si lo necesitas, pide agregar el sitio a la lista blanca o pasa a un plan de pago.
6. La cuenta gratuita tiene un tope diario de CPU; el spider es ligero pero vigílalo la primera semana. Renueva/extiende la web app cuando PythonAnywhere lo pida.

**Página**
1. En `docs/index.html` cambia `const API='data.json';` por `const API='https://USUARIO.pythonanywhere.com/data.json';`.
2. Sube `docs/index.html` a un hosting estático gratuito: GitHub Pages, Cloudflare Pages o Netlify (arrastrar y soltar).

## 6. Opción C: Raspberry Pi

Sirve cualquier Pi con Raspberry Pi OS (3, 4, 5 o Zero 2 W); el trabajo es muy ligero.

1. Instala Raspberry Pi OS Lite, activa SSH, ajusta zona horaria (`sudo timedatectl set-timezone America/Mexico_City`) y conéctala por cable si puedes.
2. Copia esta carpeta a la Pi (`scp -r reloj usuario@IP:~/`).
3. `cd ~/reloj && sudo bash raspberry/install.sh`. Instala nginx, un entorno virtual, programa el spider a las 06:00 (`/etc/cron.d/reloj`) y sirve la página desde `/var/www/reloj`.
4. `sudo nano /etc/reloj.env` → pega tu `OPENROUTER_API_KEY=`.
5. Primera corrida: `sudo -u www-data /opt/reloj/run.sh` y revisa `/var/www/reloj/data.json`.
6. Abre `http://IP_DE_LA_PI/` desde tu red local.

**Publicarla en internet (opcional, elige una):**
- **Cloudflare Tunnel** (gratis): sin abrir puertos del router; es la opción más segura.
- **Puerto 80/443 + DNS dinámico** (DuckDNS) + HTTPS con Let's Encrypt: más manual y expone tu red; mantén el sistema actualizado.
- **Híbrido:** deja la Pi solo como generadora y que suba `data.json` a un repositorio de GitHub Pages (`git push` tras el spider). Así la Pi nunca queda expuesta.

Usa una SD de buena calidad o un SSD y haz copia de `/var/www/reloj/data.json`: contiene tu historial.

## 7. Configuración que probablemente quieras cambiar

| Qué | Dónde |
|---|---|
| Medios y URLs RSS | `FEEDS` en `spider.py` (verifica la URL de Radio Fórmula; añade Reforma, DW, Al Jazeera, TASS…) |
| Fiabilidad previa por medio | `REL` en `spider.py` **y** en `docs/index.html` |
| Pesos de factores y línea base | `W`, `BASE` en ambos archivos |
| Condiciones estructurales | `STRUCT` en `spider.py` **y** `STRUCT` en `index.html` |
| Palabras clave (respaldo) | `KW` en ambos archivos |
| Modelo de IA y tope diario | `OPENROUTER_MODEL`, `del items[120:]` en `spider.py` |
| Donativos | enlaces `TU_USUARIO` / `TU_ID` de Patreon y PayPal en `index.html` |
| Anuncios | pega tu código dentro de `<div id="ad">`; AdSense además requiere su script en el `<head>` |

**Regla de oro:** todo lo que existe en `spider.py` y en `index.html` (pesos, `REL`, `BASE`, `STRUCT`, `KW`) debe quedar idéntico en ambos. Si no, el reloj de la página y el historial que guarda el spider se desfasan.

## 8. Mantenimiento

**Cada día (automático):** nada. Si quieres, abre la página y mira que "Análisis por IA" muestre titulares y que la fecha de corte sea la de hoy.

**Cada semana (5 minutos):**
- Revisa el registro de la ejecución (Actions, pestaña Tasks de PythonAnywhere o `/var/log/reloj.log`) buscando "falló" o "IA falló".
- Lee 10 justificaciones de la tabla de titulares: ¿el riesgo y la confiabilidad son razonables? Busca falsos positivos (p. ej. "war" en un titular deportivo).
- Revisa el gasto en el panel de OpenRouter.

**Cada mes:**
- Comprueba que los RSS sigan vivos (los medios cambian URLs sin avisar).
- Ajusta `REL`, palabras clave y el prompt si ves sesgos sistemáticos (p. ej., la IA premiando siempre a un bloque).
- Descarga una copia de `data.json` (historial).

**Cada trimestre:**
- Actualiza dependencias (`pip install -U feedparser`) y confirma que el modelo configurado siga disponible en OpenRouter.
- PythonAnywhere: extiende la web app. GitHub: confirma que el flujo programado no se pausó (haz un commit manual si hace falta).
- Rota la clave de API.

**Cada enero (anuncio oficial del Bulletin):**
1. Anota el nuevo valor en segundos.
2. En `index.html` agrega `[año, segundos]` al arreglo `OFF` (historial oficial) y actualiza la constante `85` (valor base) y la fecha `2026-01-27`, o las que correspondan, en la fórmula y en las gráficas.
3. Haz lo mismo con la constante `85` en `spider.py`.
4. Reajusta `BASE` para que el índice de ese día reproduzca el valor oficial y revisa `STRUCT`: elimina las condiciones que el Bulletin ya incorporó para no contarlas dos veces.

**Calibración (haz esto la primera semana):** en una prueba con pocos titulares muy corroborados de riesgo nuclear el índice se movió más de 10 segundos en un día. Si ves oscilaciones bruscas, baja el multiplicador `3` en la fórmula de aporte, o el tope `±15` por factor (en ambos archivos), hasta que los movimientos diarios sean de pocos segundos.

## 9. Solución de problemas

| Síntoma | Causa probable / solución |
|---|---|
| La página dice "sin datos del spider" | La página no encuentra `data.json`: revisa `API` y que el archivo exista; en B comprueba el CORS (`app.py`). |
| Titulares sin análisis de IA | Sin `OPENROUTER_API_KEY`, sin crédito, slug del modelo mal escrito o `openrouter.ai` bloqueado. Mira el log: "IA falló". |
| Un medio nunca aparece | URL RSS cambiada o bloqueada (lista blanca, robots, anti-bots). Prueba la URL en el navegador. |
| El historial del último mes no dibuja línea | Faltan días: necesita al menos 2 lecturas. |
| El reloj de la página no coincide con el historial | `REL`, `BASE`, `W`, `STRUCT` o `KW` distintos entre `spider.py` e `index.html`. |
| Actions no corre | Flujo pausado por inactividad o permisos: Settings → Actions → permisos de lectura y escritura. |
| JSON demasiado grande | Reduce la ventana de 45 días o el tope de 120 titulares. |

## 10. Reglas de uso responsable

- **Fuentes:** el spider solo guarda titular, enlace y fecha; no reproduzcas artículos completos. Respeta los términos y el robots.txt de cada medio y no consultes más de una vez al día.
- **Transparencia:** muestra que la estimación es experimental y no oficial; deja visibles las señales de la IA y su justificación.
- **Equilibrio:** incluye medios de todos los bloques (occidentales, rusos, chinos, latinoamericanos, árabes) y trata los estatales como fuente con sesgo propio, no como falsos por definición.
- **IA:** el modelo puede equivocarse o dejarse llevar por el encuadre de un titular. Es un apoyo, no un árbitro; mantén revisión humana periódica.
- **Dinero:** los donativos y anuncios no deben influir en `REL`, en el prompt ni en el índice. Cumple las políticas del programa de anuncios que uses (AdSense exige política de privacidad y aviso de cookies en la página alojada).
- **Datos personales:** la página guarda el historial en el `localStorage` del visitante; no recopila datos. Si añades anuncios, ellos sí pueden hacerlo.
