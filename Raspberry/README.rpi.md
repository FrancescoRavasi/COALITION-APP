# Coalition App — Raspberry Pi Setup

> Guida di installazione per **Raspberry Pi 3 Model B+** con Docker Compose.
> L'app gira in LAN locale, senza esposizione pubblica.

---

## Requisiti

| Componente | Requisito minimo |
|---|---|
| Hardware | Raspberry Pi 3 Model B+ |
| OS | Raspberry Pi OS Lite **64-bit** (Bullseye o Bookworm raccomandato) |
| Spazio SD | ≥ 4 GB liberi (il build Docker può occupare 2–3 GB) |
| RAM | 1 GB (integrata nel Pi 3B+) |
| Rete | Connessione LAN attiva |

> [!IMPORTANT]
> Usa la versione **64-bit** di Raspberry Pi OS. L'immagine `python:3.11-slim` e
> `postgres:15-alpine` sono entrambe disponibili per `arm64`. Con il SO a 32-bit
> il build funziona ma è più lento e alcune immagini potrebbero non essere disponibili.

---

## 1. Installa Docker su Raspberry Pi OS

Connettiti al Pi via SSH, poi esegui:

```bash
# Script ufficiale Docker (funziona su Debian/Raspberry Pi OS)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Aggiungi l'utente corrente al gruppo docker (evita sudo ogni volta)
sudo usermod -aG docker $USER

# Ricarica il gruppo (oppure fai logout/login)
newgrp docker

# Verifica
docker --version
docker compose version
```

> [!NOTE]
> `docker compose` (senza trattino) è il plugin moderno integrato in Docker ≥ 20.10.
> Se hai una versione più vecchia installa `docker-compose` separatamente con `pip install docker-compose`.

---

## 2. Copia i file sul Raspberry Pi

### Opzione A — via SCP (da PC Windows/Mac/Linux)

```bash
# Sostituisci PI_IP con l'IP del tuo Raspberry Pi
scp -r Raspberry/ pi@PI_IP:/home/pi/coalition/
```

Poi sul Pi:

```bash
# Entra nella cartella
cd /home/pi/coalition/
```

### Opzione B — via USB / chiavetta

Copia la cartella `Raspberry/` sulla chiavetta, montala sul Pi e copiala in `/home/pi/coalition/`.

---

## 3. Configura le variabili d'ambiente

```bash
# Sul Raspberry Pi, nella cartella coalition/
cp .env.rpi.example .env
nano .env   # oppure: vi .env
```

**Valori obbligatori da modificare:**

| Variabile | Cosa inserire |
|---|---|
| `SECRET_KEY` | Stringa random lunga (vedi comando sotto) |
| `ALLOWED_HOSTS` | IP del Pi, es. `192.168.1.100,localhost` |
| `DATABASE_URL` | Allinea password con quella in `docker-compose.yml` |
| `DISCORD_CLIENT_ID` | Dal Discord Developer Portal |
| `DISCORD_CLIENT_SECRET` | Dal Discord Developer Portal |
| `GUILD_ID` | ID numerico del server Discord |
| `DJANGO_SUPERUSER_PASSWORD` | Password admin |

Genera la `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 4. Avvio rapido

```bash
cd /home/pi/coalition/

# Build e avvio (la prima volta richiede 20-30 minuti su RPi3)
docker compose up -d --build

# Monitora i log in tempo reale
docker compose logs -f web
```

Attendi che compaia:

```
Starting server with Gunicorn...
[INFO] Listening at: http://0.0.0.0:8000
```

---

## 5. Primo accesso

1. Trova l'IP del Pi: `hostname -I`
2. Apri il browser su un altro dispositivo della LAN
3. Vai a: `http://<IP-DEL-PI>:8000`
4. Pannello admin: `http://<IP-DEL-PI>:8000/admin`
   - Username/password: quelli impostati in `.env`

---

## Gestione e aggiornamenti

### Aggiornare l'app

```bash
cd /home/pi/coalition/

docker compose down
docker compose build --no-cache
docker compose up -d
```

### Comandi utili

```bash
# Stato dei container
docker compose ps

# Log del web server
docker compose logs -f web

# Log del database
docker compose logs -f db

# Accesso alla shell Django
docker compose exec web python manage.py shell

# Backup del database
docker compose exec db pg_dump -U coalition coalition > backup_$(date +%Y%m%d).sql

# Restore del database
cat backup_YYYYMMDD.sql | docker compose exec -T db psql -U coalition coalition
```

### Riavvio automatico

I container sono configurati con `restart: unless-stopped`, quindi si riavviano
automaticamente dopo un reboot del Pi. Assicurati che il servizio Docker parta al boot:

```bash
sudo systemctl enable docker
```

---

## Note performance

> [!TIP]
> Con 2 worker Gunicorn e 1 GB di RAM il carico leggero (team piccolo, poche
> richieste concorrenti) funziona bene. Se noti lentezza, puoi ridurre a 1 worker
> impostando `--workers 1` in `entrypoint.rpi.sh`.

- **Build iniziale**: 20–30 minuti su RPi3 (compilazione dipendenze Python + Tailwind)
- **Build successive**: 5–10 minuti (layer cache Docker)
- **RAM a riposo**: ~350–450 MB con 2 worker Gunicorn + PostgreSQL
- **CPU**: Il Pi 3B+ Cortex-A53 è sufficiente per uso interno/team piccolo

> [!CAUTION]
> **Non esporre sulla rete pubblica** senza mettere nginx (o Caddy) davanti come
> reverse proxy con HTTPS. L'app in questa configurazione è pensata solo per LAN.

---

## Risoluzione problemi

### Il container `web` non parte

```bash
docker compose logs web
```

Controlla:
- `DATABASE_URL` corrisponde alle credenziali in `docker-compose.yml`
- `SECRET_KEY` è impostata e non vuota
- `ALLOWED_HOSTS` include l'IP del Pi

### Errore "port 8000 already in use"

```bash
sudo lsof -i :8000
# oppure
sudo ss -tlnp | grep 8000
```

### Reset completo (attenzione: cancella i dati!)

```bash
docker compose down -v   # rimuove anche i volumi
docker compose up -d --build
```
