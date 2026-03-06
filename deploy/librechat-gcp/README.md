# LibreChat on GCP — chat.tersona.terpedia.com

Deploy LibreChat on Google Cloud Platform and serve it at **chat.tersona.terpedia.com**. Includes TerpeneQueen (Susan Trapp, PhD) as the interviewer persona and podcast export (voice + text-to-podcast) using a trained Google voice for Susan.

## Architecture

- **LibreChat**: Docker Compose on a GCE VM (API + frontend + MongoDB + Meilisearch + RAG).
- **Domain**: `chat.tersona.terpedia.com` → GCP Load Balancer or VM external IP (DNS at your registrar).
- **SSL**: Terminated at the load balancer (Google-managed cert) or on the VM (e.g. Caddy/nginx + Let's Encrypt).
- **Podcast export**: Separate service (Cloud Run or same VM) that:
  - Saves voice conversations as podcasts (recorded audio + optional TTS for structure).
  - Converts text conversations to podcasts using TTS (TerpeneQueen/Susan Trapp custom Google voice).
- **TerpeneQueen voice**: Google Cloud Custom Voice trained from Susan Trapp’s recordings; used for TTS in podcast export (and optionally via proxy for in-chat later).

## Prerequisites

- Google Cloud project with billing enabled.
- `gcloud` CLI installed and authenticated.
- Domain `chat.tersona.terpedia.com` (or parent) manageable for DNS (e.g. terpedia.com on SiteGround; add CNAME/A for chat.tersona.terpedia.com pointing to GCP).

## 1. GCP setup (Terraform)

```bash
cd deploy/librechat-gcp/terraform
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

Then:

- Note the external IP or LB address from outputs.
- Create DNS: **CNAME** `chat.tersona.terpedia.com` → that address (or A record if using VM IP).

## 2. Deploy LibreChat (Docker Compose)

On the GCE VM (or your target host):

```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
# log out and back in

cd /opt/librechat   # or path from Terraform
cp .env.example .env
# Edit .env: MONGO_URI, API keys (OpenAI/Google/etc.), DOMAIN_CLIENT, VITE_SHARED_DOMAIN, etc.
cp docker-compose.override.yaml.example docker-compose.override.yaml
# Mount librechat.yaml and any overrides

sudo docker compose up -d
```

- **TerpeneQueen** is configured as a pre-configured assistant/agent in `librechat.yaml` (see `librechat.yaml` and `docs/TERPENEQUEEN.md`).
- **Speech (STT/TTS)** is set in `librechat.yaml` under `speech`. For in-chat voice you can use OpenAI or ElevenLabs until Susan’s Google Custom Voice is available; see `docs/GOOGLE_VOICE_SUSAN_TRAPP.md` for training and using her voice for podcast export.

## 3. SSL and domain

- **Option A — Load Balancer**: Use Terraform `lb.tf` to create an HTTPS load balancer with a Google-managed certificate for `chat.tersona.terpedia.com` and backend pointing to the VM (or instance group) port 3080.
- **Option B — VM only**: On the VM, run Caddy or nginx with Let’s Encrypt for `chat.tersona.terpedia.com` and proxy to `localhost:3080`.

Point **chat.tersona.terpedia.com** to the LB IP or the VM’s public IP in DNS.

## 4. Podcast export (voice + text-to-podcast)

- **Voice conversations → podcast**: The export service (see `podcast-export/`) can accept recorded voice conversation audio plus metadata, then produce an RSS feed + MP3 (e.g. intro/outro with TerpeneQueen TTS, then the conversation).
- **Text conversations → podcast**: The service fetches the conversation text (from LibreChat API or export), runs TTS using **Google Cloud Text-to-Speech with Susan Trapp’s custom voice** for the “host” (TerpeneQueen) segments, and generates an MP3 + RSS.

Details: `docs/PODCAST_EXPORT.md` and `podcast-export/README.md`.

## 5. Train and use Susan Trapp’s Google voice

- **Training**: Follow `docs/GOOGLE_VOICE_SUSAN_TRAPP.md` (Google Cloud Custom Voice: recordings, CSV, consent, training, deployment).
- **Usage**: Once the custom voice is deployed, the podcast-export service and any TTS proxy use that voice for “TerpeneQueen” narration.

## Files in this directory

| Path | Purpose |
|------|--------|
| `terraform/` | GCP: VPC, firewall, GCE instance (optional LB). |
| `docker-compose.yml` | LibreChat stack (from upstream + our overrides). |
| `docker-compose.override.yaml.example` | Overrides and volume mounts for GCP. |
| `.env.example` | Env vars for LibreChat (keys, domain, etc.). |
| `librechat.yaml` | LibreChat config: TerpeneQueen, speech, endpoints. |
| `podcast-export/` | Service to save voice/text convos as podcasts (TTS = Susan’s voice). |
| `docs/TERPENEQUEEN.md` | TerpeneQueen persona and LibreChat setup. |
| `docs/PODCAST_EXPORT.md` | Podcast export design and API. |
| `docs/GOOGLE_VOICE_SUSAN_TRAPP.md` | Google Custom Voice training for Susan Trapp. |

## Quick checklist

- [ ] GCP project created, billing on, APIs enabled.
- [ ] Terraform applied; VM (and optional LB) created.
- [ ] DNS: `chat.tersona.terpedia.com` → GCP (LB or VM IP).
- [ ] SSL in place (LB or Caddy/nginx on VM).
- [ ] LibreChat `.env` and `librechat.yaml` configured (TerpeneQueen, speech).
- [ ] LibreChat running (`docker compose up -d`).
- [ ] Podcast-export service deployed and configured (optional).
- [ ] Susan Trapp’s custom voice trained and deployed in GCP; podcast-export (and any TTS proxy) use it for TerpeneQueen.
