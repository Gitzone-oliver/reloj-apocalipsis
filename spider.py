# pip install --user feedparser   |   Tasks: OPENROUTER_API_KEY=sk-or-... python3 /home/USUARIO/spider.py
# Sin OPENROUTER_API_KEY (o si la API falla) usa el análisis por palabras clave.
# Verifica que openrouter.ai esté en la whitelist de tu cuenta.
# Cuenta gratis: solo salen peticiones a sitios de la whitelist; revisa que
# cada RSS esté permitido (los que fallen se omiten sin romper el resto).
import feedparser, json, re, os, urllib.request, datetime as dt
feedparser.USER_AGENT = "Mozilla/5.0 (investigacion; reloj-apocalipsis)"
OUT = os.environ.get("DATA_PATH", "/home/USUARIO/data.json")
D = dt.date
FEEDS = {
 "CNN": ("http://rss.cnn.com/rss/edition_world.rss", 0),
 "NYTimes": ("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", 0),
 "BBC": ("http://feeds.bbci.co.uk/news/world/rss.xml", 0),
 "RT": ("https://www.rt.com/rss/news/", 0),
 "Radio Fórmula": ("https://www.radioformula.com.mx/rss", 0),   # verificar URL
 "Reddit r/worldnews": ("https://www.reddit.com/r/worldnews/.rss", 1),  # rumor
}
REL = {"Reuters":.95,"NYTimes":.9,"BBC":.9,"CNN":.8,"Reforma":.8,"Radio Fórmula":.7,"RT":.5,"Reddit r/worldnews":.3}
W = dict(N=.40, C=.25, B=.15, I=.10, G=.10)
BASE = dict(N=78, C=70, B=55, I=60, G=75)
STRUCT = [("N", 3), ("N", 2)]
KW = {k: (re.compile(u, re.I), re.compile(d, re.I)) for k, (u, d) in {
 "N": (r"nuclear|oreshnik|icbm|warhead|ojiva|misil|new start|escalat|escalada|nuke", r"arms control deal|desarme|treaty signed|acuerdo nuclear|de-escalat|desescalad"),
 "C": (r"heatwave|ola de calor|record temperature|wildfire|incendio|flood|inundaci|hurricane|huracán|emissions rise|coal", r"climate deal|acuerdo climático|emissions fall|renewable record|cop\d+ agree"),
 "B": (r"pandemic|pandemia|outbreak|brote|h5n1|avian flu|gripe aviar|virus|bioweapon|lab leak", r"vaccine approved|vacuna aprobada|outbreak contained|brote controlado"),
 "I": (r"artificial intelligence|inteligencia artificial|\bai\b|deepfake|autonomous weapon|agi|chatbot", r"ai treaty|ai regulation passed|regulaci[oó]n de ia|ai safety agreement"),
 "G": (r"war|guerra|invasion|invasión|strike|ataque|sanction|sanciones|tension|tensión|ceasefire collapse|missile strike", r"ceasefire|alto el fuego|peace talks|negociaciones de paz|peace deal"),
}.items()}

def relevant(t):
    return any(u.search(t) or d.search(t) for u, d in KW.values())

def score(items, today):
    adj = {k: 0.0 for k in W}
    for f, v in STRUCT: adj[f] += v
    hits = {k: {} for k in W}
    aip = {k: 0.0 for k in W}
    for n in items:
        a = (today - D.fromisoformat(n["date"])).days
        if a not in range(0, 46): continue
        rel, dec = REL.get(n["src"], .5), .5 ** (a / 20)
        if "ai" in n:
            if n["ai"]["f"] in W:
                aip[n["ai"]["f"]] += n["ai"]["risk"] / 5 * n["ai"]["rel"] * dec * 3
            continue
        for f, (u, d) in KW.items():
            up, dn = u.search(n["title"]), d.search(n["title"])
            if up or dn:
                hits[f].setdefault(n["src"], []).append((-1 if dn else 1, rel, dec, n.get("rumor", 0)))
    for f, h in hits.items():
        corro = sum(1 for s in h if REL.get(s, .5) > .35)
        tot = 0
        for s, lst in h.items():
            for sev, rel, dec, rum in lst:
                p = sev * rel * dec * 1.2
                if rum and sev > 0 and corro < 3: p = 0
                if corro >= 3 and sev > 0: p *= 1.25
                tot += p
        adj[f] += max(-15, min(15, tot + aip[f]))
    R = sum(W[k] * max(0, min(100, BASE[k] + adj[k])) for k in W)
    R0 = sum(W[k] * BASE[k] for k in W)
    return round(max(1, min(600, 85 * (100 - R) / (100 - R0))), 1)

# Modelo de OpenRouter: copia el "slug" exacto de openrouter.ai/models (ej. proveedor/modelo).
# Puedes cambiarlo sin tocar el codigo con la variable OPENROUTER_MODEL.
MODEL = os.environ.get("OPENROUTER_MODEL") or "openai/gpt-4o-mini"
KEY = os.environ.get("OPENROUTER_API_KEY", "")
PROMPT = """Eres analista de riesgo global para un índice tipo Reloj del Apocalipsis.
Para cada titular devuelve SOLO una lista JSON de objetos:
{"i": n, "f": "N|C|B|I|G|none", "risk": -5 a 5, "rel": 0 a 1, "flags": [...], "why": "máx. 15 palabras"}
f: N nuclear, C clima, B biológico, I inteligencia artificial, G geopolítica.
risk positivo aumenta el riesgo, negativo lo reduce, 0 si es irrelevante.
rel = confiabilidad según: fuente (rumor=1 es extraoficial; los medios estatales tienen sesgo propio),
estilo (lenguaje cargado, sensacionalismo, atribución anónima, falta de datos), replicación
(rep = medios que lo repiten; rum = fuentes extraoficiales) y plausibilidad.
Un hecho repetido por medios de bloques opuestos pesa más. Un rumor sin corroboración: rel máximo 0.3.
flags posibles: sensacionalista, lenguaje_cargado, fuente_anonima, estatal, sin_corroborar,
corroborado, opinion, propaganda_probable."""

def toks(t):
    return set(re.findall(r"\w{4,}", t.lower()))

def replication(items):
    T = [toks(n["title"]) for n in items]
    for i, n in enumerate(items):
        rep, rum = set(), set()
        for j, m in enumerate(items):
            if i == j or m["src"] == n["src"]: continue
            u = T[i].union(T[j])
            if u and len(T[i].intersection(T[j])) / len(u) >= .3:
                (rum if m.get("rumor") else rep).add(m["src"])
        n["rep"], n["rum"] = sorted(rep), sorted(rum)

def analyze(items):
    if not KEY or not items: return
    del items[120:]   # tope diario de costo
    replication(items)
    lines = [{"i": k, "src": n["src"], "rumor": n.get("rumor", 0), "title": n["title"],
              "rep": n["rep"], "rum": n["rum"]} for k, n in enumerate(items)]
    body = json.dumps({"model": MODEL, "max_tokens": 8000, "temperature": 0.2,
        "messages": [{"role": "system", "content": PROMPT},
                     {"role": "user", "content": json.dumps(lines, ensure_ascii=False)}]}).encode()
    rq = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body,
        {"content-type": "application/json", "Authorization": "Bearer " + KEY,
         "X-Title": "reloj-apocalipsis"})
    try:
        txt = json.load(urllib.request.urlopen(rq, timeout=180))["choices"][0]["message"]["content"]
        res = json.loads(re.search(r"\[.*\]", txt, re.S).group(0))
    except Exception as ex:
        print("IA falló, se usan palabras clave:", ex); return
    for r in res:
        try:
            n = items[int(r["i"])]
            prior = REL.get(n["src"], .5)
            ai = min(1, max(0, float(r["rel"])))
            rsc = min(1, (len(n["rep"]) + .5 * len(n["rum"])) / 3)
            n["ai"] = {"f": r["f"] if r["f"] in W else None,
                       "risk": max(-5, min(5, float(r["risk"]))),
                       "rel": round(.35 * prior + .40 * ai + .25 * rsc, 2),   # fuente + IA + replicación
                       "flags": [str(x) for x in r.get("flags", [])][:4],
                       "why": str(r.get("why", ""))[:120],
                       "rep": len(n["rep"]), "rum": len(n["rum"])}
        except Exception:
            pass

old = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
today = D.today()
seen, arch = set(), []
new = []
for src, (url, rumor) in FEEDS.items():
    try:
        for e in feedparser.parse(url).entries[:80]:
            if relevant(e.title):
                new.append({"src": src, "title": e.title, "url": e.link,
                            "date": today.isoformat(), "rumor": rumor})
    except Exception as ex:
        print(src, "falló:", ex)
analyze(new)
for n in new + old.get("news", []):
    k = (n["src"], n["title"])
    if k in seen or (today - D.fromisoformat(n["date"])).days > 45: continue
    seen.add(k); arch.append(n)
hist = old.get("history", {})
hist[today.isoformat()] = score(arch, today)
json.dump({"updated": today.isoformat(), "news": arch, "history": hist},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
