# HTTPS / health endpoint failing — troubleshooting

If **https://chat.tersona.terpedia.com/health** fails (timeout, connection refused, or SSL error), work through these checks.

## 1. DNS must point to the load balancer

**From your machine:**
```bash
dig +short chat.tersona.terpedia.com
# Must return: 34.110.252.202
```

- If it returns nothing or a different IP:
  - **Using Route 53:** Ensure your **registrar** has the terpedia.com **nameservers** set to the Route 53 delegation set (see `deploy/ROUTE53_SETUP_COMPLETE.md`). Until that’s done, Route 53 records don’t apply.
  - **Using another DNS (e.g. SiteGround):** Add an **A record**: `chat.tersona.terpedia.com` → `34.110.252.202`.
- Wait 5–60 minutes for DNS to propagate, then run `dig` again.

## 2. Google-managed SSL certificate must be ACTIVE

The load balancer only serves HTTPS after the managed cert is issued. Issuance happens only when:

- DNS for `chat.tersona.terpedia.com` resolves to **34.110.252.202** (step 1).
- Google’s verification can reach that IP (usually a few minutes to ~1 hour).

**Check in GCP Console:**

1. Open [Network Services → Load balancing](https://console.cloud.google.com/net-services/loadbalancing/list/loadBalancers?project=terpedia-489015).
2. Click the load balancer (e.g. **librechat-https-rule** or the one with IP **34.110.252.202**).
3. Check **Frontend** / **SSL certificate** — status should be **Active**. If it’s **Provisioning** or **Failed**, wait or fix DNS and try again.

**CLI (after `gcloud auth login`):**
```bash
gcloud compute ssl-certificates list --project=terpedia-489015
# STATUS should be ACTIVE for librechat-ssl-cert
```

Until the cert is **ACTIVE**, https://chat.tersona.terpedia.com will not work.

## 3. Backend and VM

If DNS and cert are correct but the site still doesn’t load:

- **Backend health:** In the same load balancer in the console, check that the **Backend** is **Healthy** (health check uses path `/` on port 3080).
- **VM/containers:** SSH to the LibreChat VM and confirm the app is listening and `/health` returns 200:
  ```bash
  gcloud compute ssh librechat --zone=us-central1-a --project=terpedia-489015
  curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3080/health   # expect 200
  sudo docker compose -f /opt/librechat/docker-compose.yml ps
  ```

## 4. Quick reference

| Item        | Value                    |
|------------|---------------------------|
| LB IP      | 34.110.252.202           |
| Domain     | chat.tersona.terpedia.com |
| Health URL | https://chat.tersona.terpedia.com/health |
| Route 53   | A record → 34.110.252.202 (profile terpedia) |

Most “health failed” cases are **DNS not pointing to 34.110.252.202** or **SSL certificate still Provisioning**. Fix DNS first, then wait for the cert to become Active.
