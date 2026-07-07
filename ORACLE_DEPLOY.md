# Deploy Trade Mentor free & always-on (Oracle Cloud Always Free)

This runs the whole system — Postgres/TimescaleDB, the API + built frontend, and
the 24/7 learning loop — on an **Oracle Cloud Always Free** ARM VM, behind
**Caddy** with automatic HTTPS, on a free **DuckDNS** domain. Cost: **$0/month**,
and it never sleeps, so the loop keeps ingesting, predicting, resolving and
retraining around the clock.

> Why not a free web host (Render/Railway/Fly free tiers)? Those sleep when
> idle, which kills the scheduler — no sleeping means no "always learning".
> An Always Free VM is a real, always-on Linux box, so the loop runs for real.

---

## 0. What you'll end up with

- `https://<you>.duckdns.org` → login page, served over HTTPS.
- Postgres data and the trained models persisted on the VM's disk.
- The loop enabled: fresh bars pulled hourly, predictions logged and resolved,
  weekly retrain-and-promote.

Total time: ~30–45 min, most of it waiting on Oracle's VM to provision.

---

## 1. Create the Always Free VM

1. Sign up at <https://www.oracle.com/cloud/free/> (needs a card for identity
   verification — Always Free resources are never charged). Pick a home region
   close to you.
2. Console → **Compute → Instances → Create instance**.
   - **Image:** Canonical **Ubuntu 22.04**.
   - **Shape:** Change shape → **Ampere (Arm)** → `VM.Standard.A1.Flex`. Set
     **2 OCPUs / 12 GB RAM** (well within Always Free; comfortable for this app).
     If you see "out of capacity", try again later or pick another availability
     domain — Arm capacity comes and goes.
   - **SSH keys:** let it generate a key pair and **download the private key**
     (or paste your own public key).
   - **Boot volume:** default (~47 GB) is plenty.
   - Create.
3. When it's running, copy the **public IPv4 address**.

### Open the firewall (two layers)

Oracle blocks inbound ports by default in **two** places — do both:

- **Security List (VCN):** Console → Networking → your VCN → the public subnet →
  its Security List → **Add Ingress Rules**: source `0.0.0.0/0`, TCP,
  destination ports **80** and **443** (two rules, or a comma list).
- **Host firewall:** you'll run the `ufw` / `iptables` commands in step 3.

---

## 2. Get a free domain (DuckDNS)

Caddy needs a real hostname to get a TLS certificate.

1. Go to <https://www.duckdns.org>, sign in (GitHub/Google).
2. Create a subdomain, e.g. `tradementor` → you get `tradementor.duckdns.org`.
3. Set its IP to your VM's **public IPv4** and click **update**.
4. Verify from your laptop: `ping tradementor.duckdns.org` should show the VM IP.

---

## 3. Connect and install Docker

SSH in (from where you saved the private key):

```bash
chmod 600 ./your-key.key
ssh -i ./your-key.key ubuntu@<VM_PUBLIC_IP>
```

Install Docker Engine + the compose plugin, and open the host firewall:

```bash
# Docker (official convenience script)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu        # run docker without sudo
# Host firewall: allow SSH + web
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save        # persist the rules across reboots
```

Log out and back in (`exit`, then SSH again) so the docker group applies.

---

## 4. Get the code and set secrets

```bash
git clone https://github.com/Hassoun1001/mentor.git
cd mentor
```

Generate the two secrets. Run the password hasher through Docker so you don't
need Python on the VM (uses the app image you're about to build):

```bash
# Build the app image once (also used by compose later):
docker build -t mentor-app .

# 1) A bcrypt hash of your login password:
docker run --rm -it mentor-app python -m mentor.cli.hash_password
#   → paste/type your password, copy the printed $2b$... hash.

# 2) A 48-byte JWT secret:
openssl rand -base64 48
```

Create `.env` next to the compose file:

```bash
nano .env
```

```dotenv
# --- required ---
MENTOR_DOMAIN=tradementor.duckdns.org
MENTOR_DB_PASSWORD=<a long random password>
MENTOR_AUTH_USERNAME=mentor
MENTOR_AUTH_PASSWORD_HASH=<the $2b$... hash from step above>
MENTOR_JWT_SECRET=<the openssl output>

# --- optional but recommended ---
TWELVE_DATA_API_KEY=<free key from twelvedata.com for better intraday data>
ANTHROPIC_API_KEY=<if you want the LLM mentor chat>

# The loop is ON by default in this compose; leave as-is for always-learning.
# MENTOR_LOOP_ENABLED=true
```

Save (Ctrl-O, Enter, Ctrl-X). Lock it down: `chmod 600 .env`.

---

## 5. Launch

```bash
docker compose -f docker-compose.caddy.yml up -d --build
```

This builds the frontend + backend image, starts Postgres, runs DB migrations
on boot, starts the app (loop enabled), and starts Caddy — which fetches a
Let's Encrypt certificate for your domain automatically (give it ~30 seconds).

Check it:

```bash
docker compose -f docker-compose.caddy.yml ps          # all "running"/"healthy"
docker compose -f docker-compose.caddy.yml logs -f caddy   # watch cert issuance
docker compose -f docker-compose.caddy.yml logs -f app     # watch the loop
```

Open `https://tradementor.duckdns.org` — you should get the login page over
HTTPS. Log in with `MENTOR_AUTH_USERNAME` and the password you hashed.

---

## 6. Backfill history so the models have something to learn from

The loop keeps data *fresh*, but on a brand-new box the DB is empty. Backfill a
few years of bars once (adjust dates as you like):

```bash
docker compose -f docker-compose.caddy.yml exec app \
  python -m mentor.cli.ingest --symbol EURUSD --timeframe 1h \
  --start 2021-01-01 --end 2026-07-01
```

After that the hourly loop tops it up on its own.

---

## 7. Day-to-day operations

| Task | Command (run in `~/mentor`) |
| --- | --- |
| Update to latest code | `git pull && docker compose -f docker-compose.caddy.yml up -d --build` |
| View app logs | `docker compose -f docker-compose.caddy.yml logs -f app` |
| Restart everything | `docker compose -f docker-compose.caddy.yml restart` |
| Stop | `docker compose -f docker-compose.caddy.yml down` |
| Back up the database | `docker compose -f docker-compose.caddy.yml exec db pg_dump -U mentor mentor > backup_$(date +%F).sql` |

Postgres data lives in the `mentor_db_data` Docker volume and the TLS certs in
`caddy_data`, so `down` (without `-v`) and reboots keep your data and cert.

---

## Security notes

- The app image refuses to start in production if `MENTOR_AUTH_PASSWORD_HASH`,
  `MENTOR_JWT_SECRET`, or `MENTOR_DB_PASSWORD` are unset/placeholder — so a
  misconfigured box fails closed instead of serving an open API.
- Only 80/443 are exposed to the internet; the app (8000) and Postgres are on
  Docker's internal network only.
- Keep `.env` at `chmod 600`; it holds all your secrets.
- Consider restricting SSH (22) in the Oracle Security List to your own IP.

For non-Oracle / PaaS options see [DEPLOY.md](DEPLOY.md).
