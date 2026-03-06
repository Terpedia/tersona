# LibreChat GCP Deployment - COMPLETED

## ✅ Infrastructure Deployed

### Resources Created:
- **GCP Project**: terpedia-489015
- **VM Instance**: librechat (e2-standard-4, Ubuntu 22.04)
  - Location: us-central1-a
  - No external IP (internal only + IAP)
- **Load Balancer IP**: 34.110.252.202
- **SSL Certificate**: Google-managed SSL for chat.tersona.terpedia.com
- **Cloud NAT**: Enabled for VM outbound internet access
- **Firewall Rules**: HTTP (80), HTTPS (443), App (3080)

### Services Running:
- ✅ LibreChat (port 3080)
- ✅ MongoDB (data storage)
- ✅ Meilisearch (conversation search)
- ✅ Speech-bridge (Google STT/TTS)

## 🚀 Next Steps

### 1. Configure DNS (REQUIRED)
Point `chat.tersona.terpedia.com` to the load balancer:

**Load Balancer IP**: `34.110.252.202`

#### If using SiteGround (for terpedia.com):
1. Log into SiteGround control panel
2. Go to Domain → DNS Zone Editor
3. Add/Update A record:
   - **Name**: `chat.tersona.terpedia.com`
   - **Type**: A
   - **Value**: `34.110.252.202`
   - **TTL**: 14400 (or default)

#### Alternative: If terpedia.com DNS is elsewhere:
Add an A record pointing `chat.tersona.terpedia.com` → `34.110.252.202`

### 2. Wait for SSL Certificate Provisioning
- Google-managed SSL cert needs DNS to be pointing to the load balancer
- Takes 15-60 minutes after DNS propagates
- Check status: `gcloud compute ssl-certificates describe librechat-ssl-cert --global --project=terpedia-489015`

### 3. Create TerpeneQueen Agent in LibreChat
Once the site is accessible at https://chat.tersona.terpedia.com:

1. Create an account/login
2. Go to Agents section
3. Create a new agent with:
   - **Name**: TerpeneQueen
   - **Model**: gemini-2.0-flash-001 (or your preference)
   - **System Prompt**: See `docs/TERPENEQUEEN.md`

### 4. Train Susan Trapp's Custom Voice (Optional)
See `docs/GOOGLE_VOICE_SUSAN_TRAPP.md` for instructions on training a Google Custom Voice.

## 🔧 Management Commands

### SSH to VM:
```bash
gcloud compute ssh librechat --zone=us-central1-a --project=terpedia-489015
```

### View Logs:
```bash
cd /opt/librechat
sudo docker compose logs -f [service-name]
# service-name: api, mongodb, meilisearch, speech-bridge
```

### Restart Services:
```bash
cd /opt/librechat
sudo docker compose restart
```

### Update Configuration:
1. Edit files locally in `deploy/librechat-gcp/`
2. Copy to VM:
```bash
cd /Users/danielmcshan/GitHub/tersona/deploy/librechat-gcp
gcloud compute scp .env librechat.yaml librechat:~/
gcloud compute ssh librechat --command="sudo mv ~/.env ~/librechat.yaml /opt/librechat/ && cd /opt/librechat && sudo docker compose restart api"
```

## 📝 Configuration Files

- `.env` - Environment variables (API keys, domain, etc.)
- `librechat.yaml` - LibreChat config (speech, agents, endpoints)
- `docker-compose.yml` - Service definitions
- `auth.json` - Google Cloud service account credentials

## ⚠️ Important Notes

1. **API Keys**: Your `.env` contains sensitive API keys. Never commit it to git.
2. **Service Account**: `auth.json` contains Google Cloud credentials for speech services.
3. **Backups**: MongoDB data is in `/opt/librechat/data-node` on the VM. Set up regular backups.
4. **SSL**: The certificate is provisioned AFTER DNS points to the load balancer. Be patient.
5. **Costs**: Monitor GCP costs (VM, load balancer, NAT gateway, API calls).

## 🔗 URLs

- **Public URL** (after DNS): https://chat.tersona.terpedia.com
- **VM Internal**: http://10.128.0.2:3080 (or similar, check with `ip addr`)
- **Speech Bridge**: http://localhost:8001 (on VM only)

## 📚 Documentation

- Main README: `../README.md`
- TerpeneQueen Setup: `docs/TERPENEQUEEN.md`
- Podcast Export: `docs/PODCAST_EXPORT.md`
- Custom Voice Training: `docs/GOOGLE_VOICE_SUSAN_TRAPP.md`
- Service Account Setup: `docs/SERVICE_ACCOUNT_SETUP.md`

## 🎯 Summary

LibreChat is deployed and running on GCP with:
- ✅ Terraform infrastructure
- ✅ Docker containers running
- ✅ Google Gemini integration
- ✅ Google Speech bridge (STT/TTS)
- ✅ Load balancer with SSL
- ⏳ DNS configuration (you need to do this)
- ⏳ TerpeneQueen agent creation (after DNS)
- ⏳ Custom voice training (optional, later)
