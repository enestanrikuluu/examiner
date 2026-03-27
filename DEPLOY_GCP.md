# Deploying Examiner on Google Cloud (Free Trial)

This guide walks you through deploying the Examiner app on a GCP free trial VM, then migrating to Hetzner when the $300 credits run out.

---

## Part 1: GCP Setup (One-Time)

### 1.1 Create your GCP account

1. Go to https://cloud.google.com/free
2. Click **Get started for free**
3. Sign in with your Google account
4. Enter billing info (you won't be charged — GCP requires a card but the free trial is no-charge)
5. You'll see **$300 in credits, valid for 90 days**

### 1.2 Create a VM instance

1. Go to **Compute Engine** > **VM instances** (it may take a minute to enable the API on first use)
2. Click **Create Instance**
3. Configure it like this:

| Setting | Value |
|---------|-------|
| **Name** | `examiner` |
| **Region** | `us-central1` (Iowa) — cheapest |
| **Zone** | `us-central1-a` |
| **Machine type** | `e2-standard-2` (2 vCPU, 8 GB RAM) |
| **Boot disk** | Ubuntu 22.04 LTS, **30 GB SSD** |
| **Firewall** | Check both **Allow HTTP** and **Allow HTTPS** |

> **Cost**: ~$50/month, but covered by your $300 credits for ~6 months worth of usage (you have 90 days to use them).

3. Click **Create** and wait for the VM to start.

### 1.3 Note your External IP

Once the VM is running, copy the **External IP** shown in the VM list. You'll need it throughout this guide. We'll call it `YOUR_IP` below.

---

## Part 2: Server Setup

### 2.1 SSH into your VM

The easiest way: click the **SSH** button next to your VM in the GCP Console. This opens a browser terminal.

Or from your local machine:

```bash
gcloud compute ssh examiner --zone us-central1-a
```

### 2.2 Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Let your user run docker without sudo
sudo usermod -aG docker $USER

# Log out and back in for group change to take effect
exit
```

SSH back in, then verify:

```bash
docker --version
docker compose version
```

### 2.3 Clone your repo

```bash
git clone https://github.com/YOUR_USERNAME/examiner.git
cd examiner
```

> If your repo is private, you'll need a GitHub personal access token or SSH key.

---

## Part 3: Configure and Deploy

### 3.1 Generate your secrets

```bash
# Generate a JWT secret
openssl rand -hex 32
# Copy the output — you'll need it below

# Generate a Postgres password
openssl rand -hex 16
# Copy this too

# Generate a MinIO secret
openssl rand -hex 16
# Copy this too
```

### 3.2 Create your .env file

```bash
cp .env.production .env
nano .env
```

Fill in these values (replace the placeholders):

```env
POSTGRES_PASSWORD=<your generated postgres password>
JWT_SECRET=<your generated jwt secret>
MINIO_SECRET_KEY=<your generated minio secret>

ANTHROPIC_API_KEY=<your Anthropic API key>
# GROQ_API_KEY=<optional, if you have one>

CORS_ORIGINS=http://YOUR_IP
NEXT_PUBLIC_API_URL=/api/v1
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

### 3.3 Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

This will:
- Build all Docker images (first run takes 5-10 minutes)
- Start Postgres, Redis, and MinIO
- Run database migrations
- Start the API, worker, frontend, and Nginx
- Run health checks

When it finishes, you should see:

```
=========================================
[INFO] Deployment complete!
=========================================

[INFO] App is running at: http://YOUR_IP:80
```

### 3.4 Verify it works

Open `http://YOUR_IP` in your browser. You should see the Examiner frontend.

---

## Part 4: GCP-Specific Configuration

### 4.1 Set up a static IP (so your IP doesn't change on reboot)

1. Go to **VPC Network** > **IP addresses** in GCP Console
2. Find your VM's IP and click **Reserve** to make it static
3. This is free while the VM is running

### 4.2 Set up a basic firewall (already done if you checked HTTP/HTTPS)

Verify your firewall rules allow port 80:

```bash
gcloud compute firewall-rules list --filter="allowed:tcp:80"
```

### 4.3 Set up daily Postgres backups

Create a backup script:

```bash
mkdir -p ~/backups

cat > ~/backup-db.sh << 'SCRIPT'
#!/bin/bash
cd ~/examiner
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U examiner examiner | gzip > ~/backups/examiner_${TIMESTAMP}.sql.gz

# Keep only last 7 days
find ~/backups -name "examiner_*.sql.gz" -mtime +7 -delete
echo "[$(date)] Backup complete: examiner_${TIMESTAMP}.sql.gz"
SCRIPT

chmod +x ~/backup-db.sh
```

Add it to cron (runs daily at 3 AM):

```bash
(crontab -l 2>/dev/null; echo "0 3 * * * /home/$USER/backup-db.sh >> /home/$USER/backups/backup.log 2>&1") | crontab -
```

### 4.4 (Optional) Add a domain name

If you have a domain, point an A record to `YOUR_IP`, then update your `.env`:

```env
CORS_ORIGINS=http://yourdomain.com
```

Restart:

```bash
cd ~/examiner && docker compose up -d
```

---

## Part 5: Monitoring Your Credits

Check your remaining credits at: https://console.cloud.google.com/billing

GCP will email you when credits are running low. You'll have time to migrate.

---

## Part 6: Migrating to Hetzner (When Credits Run Out)

This is the easy part — your app is fully containerized, so the migration is just "same steps, different server."

### 6.1 Create a Hetzner server

1. Sign up at https://www.hetzner.com/cloud
2. Create a **CX32** server (4 vCPU, 8 GB RAM) — ~€7.50/month
3. Select **Ubuntu 22.04**, choose a location (Falkenstein is cheapest)

### 6.2 Back up your GCP data

On your GCP VM:

```bash
cd ~/examiner

# Dump the database
docker compose exec -T postgres pg_dump -U examiner examiner | gzip > ~/examiner-final-backup.sql.gz

# Grab your .env (has all your config)
cp .env ~/examiner-env-backup
```

Download both files to your local machine:

```bash
# From your LOCAL machine
gcloud compute scp examiner:~/examiner-final-backup.sql.gz .
gcloud compute scp examiner:~/examiner-env-backup .
```

### 6.3 Set up Hetzner (same as Part 2-3)

SSH into your new Hetzner server, install Docker, clone the repo, copy your `.env` over, and update the IP:

```bash
# On Hetzner
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in

git clone https://github.com/YOUR_USERNAME/examiner.git
cd examiner

# Copy your backed up .env, update CORS_ORIGINS with new Hetzner IP
nano .env

./deploy.sh
```

### 6.4 Restore your database

```bash
# Copy backup to Hetzner (from your local machine)
scp examiner-final-backup.sql.gz root@HETZNER_IP:~/examiner/

# On Hetzner, restore into the running Postgres
cd ~/examiner
gunzip -c examiner-final-backup.sql.gz | docker compose exec -T postgres psql -U examiner examiner
```

### 6.5 Update DNS (if using a domain)

Point your A record to the new Hetzner IP. Done.

### 6.6 Delete the GCP VM

Go to Compute Engine > VM instances, select `examiner`, and delete it. This stops all billing.

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `docker compose ps` | Check service status |
| `docker compose logs -f api` | Follow API logs |
| `docker compose logs -f worker` | Follow worker logs |
| `docker compose restart` | Restart all services |
| `docker compose down` | Stop everything |
| `docker compose up -d --build` | Rebuild and restart |
| `./deploy.sh` | Full redeploy |

---

## Estimated Timeline

| Phase | Duration | Cost |
|-------|----------|------|
| GCP free trial | Up to 90 days | $0 (covered by $300 credits) |
| Migration to Hetzner | ~1 hour | One-time effort |
| Hetzner ongoing | Indefinite | ~$8/month |
