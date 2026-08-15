# Idealista bot (MVP personal)

Chequea una búsqueda de Idealista cada pocos minutos, detecta anuncios nuevos y
te avisa por Telegram con un **borrador de mensaje** listo para que tú se lo
mandes al dueño a mano.

**Importante:** el bot solo *lee* la web (anuncios públicos, sin login) y te
escribe a ti. No manda mensajes en Idealista ni usa tu cuenta → no hay riesgo de
que te bloqueen la cuenta. El único bloqueo posible es de IP, y por eso usamos
ScrapingBee (que salta DataDome) y una frecuencia con jitter.

## Cómo funciona

```
cada ~5 min:
  1 request a la búsqueda ordenada por fecha  (vía ScrapingBee)
  parsea IDs de anuncio
  ¿ID nuevo? -> Claude redacta borrador -> Telegram te avisa con enlace + borrador
  tú abres el enlace y mandas el mensaje a mano
```

## Puesta en marcha

```bash
cd idealista-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # y rellena los valores
python main.py
```

### Qué necesitas en el `.env`

| Variable | De dónde sale |
|---|---|
| `SEARCH_URL` | La URL de tu búsqueda en Idealista |
| `BRIGHTDATA_API_KEY` + `BRIGHTDATA_ZONE` | brightdata.com → crea una zona "Web Unlocker" y un API token |
| `ANTHROPIC_API_KEY` | console.anthropic.com (o usa `ant auth login`) |
| `TELEGRAM_BOT_TOKEN` | Telegram, hablando con `@BotFather` (`/newbot`) |
| `TELEGRAM_CHAT_ID` | `https://api.telegram.org/bot<TOKEN>/getUpdates` tras escribirle a tu bot |

## Coste

- **Bright Data Web Unlocker**: el grueso del coste. ~1 request/ciclo, pagas
  solo los que salen bien (~$1,5-3 / 1.000). Con chequeos cada 30 min de 6am a
  2am son ~1.200 requests/mes → **~$2-5/mes**.
- **Claude**: solo cuando hay anuncio nuevo. Con `claude-haiku-4-5` (por defecto)
  cada borrador cuesta céntimos. Cámbialo con `CLAUDE_MODEL` si quieres otro.
- **Telegram**: gratis.

## Opción B: correrlo gratis en GitHub Actions

En vez de un servidor, GitHub lo ejecuta cada 30 min. El estado (anuncios ya
vistos) se guarda en `state.json`, que el propio workflow versiona en el repo.

1. Crea un repo en GitHub (**privado** recomendado) y sube esta carpeta:
   ```bash
   cd idealista-bot
   git init && git add . && git commit -m "idealista bot"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
   git push -u origin main
   ```
   (El `.gitignore` ya evita subir el `.env` con tus claves.)
2. En el repo: **Settings → Secrets and variables → Actions → New repository secret**.
   Crea estos 5 secrets (los mismos valores que tenías en el `.env`):
   `SEARCH_URL`, `BRIGHTDATA_API_KEY`, `BRIGHTDATA_ZONE`, `TELEGRAM_BOT_TOKEN`,
   `TELEGRAM_CHAT_ID`.
3. **Settings → Actions → General → Workflow permissions → Read and write
   permissions** (para que pueda guardar `state.json`).
4. Pestaña **Actions → idealista-bot → Run workflow** para probarlo a mano.
   El primer run marca lo existente como visto (sin avisar); a partir de ahí solo
   te avisa de lo nuevo.

Nota: el cron de GitHub a veces se retrasa (no es tan puntual como un VPS). Para
validar va perfecto; si luego quieres máxima puntualidad, pásate a la opción VPS.

## Dónde correrlo en un servidor (VPS / Raspberry Pi)

- Cualquier VPS barato (Hetzner/DigitalOcean ~4-5 €/mes) con `nohup python main.py &`
  o un servicio `systemd`.
- Mientras pruebas, tu propia máquina vale.

## Notas de mantenimiento

- Si ves en el log `0 anuncios` de forma repetida, Idealista habrá cambiado las
  clases HTML: hay que ajustar los selectores en `scraper.py` (`parse_listings`).
- El primer arranque marca todo lo existente como visto **sin avisar**, para no
  recibir un aluvión. A partir de ahí solo avisa de lo nuevo.
- El estado vive en `seen.sqlite3`. Bórralo si quieres empezar de cero.
