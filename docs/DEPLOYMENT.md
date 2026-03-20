# Deploy TerpeneQueen Chat to tersona.terpedia.com

This guide walks through deploying the TerpeneQueen chat interface to **tersona.terpedia.com** using GitHub Pages.

## Prerequisites

- GitHub repository: `tersona` (or your repo name)
- Domain: `tersona.terpedia.com` DNS access (via Route 53 or your registrar)
- Google Gemini API key (users will enter their own)

## Step 1: Enable GitHub Pages

1. Go to your repository on GitHub
2. **Settings** → **Pages**
3. Under **Source**, select:
   - **Deploy from a branch**
   - **Branch**: `main` (or `gh-pages`)
   - **Folder**: `/docs`
4. Click **Save**

GitHub will now build and deploy from the `docs/` folder. Your site will be available at:
- `https://your-username.github.io/tersona/` (or your repo name)

## Step 2: Configure Custom Domain

1. In **Settings** → **Pages**, scroll to **Custom domain**
2. Enter: `tersona.terpedia.com`
3. Click **Save**
4. GitHub will create a `CNAME` file in your repo (or you can create it manually)

## Step 3: Update DNS

You have two options:

### Option A: Route 53 (if terpedia.com uses Route 53)

```bash
# Add CNAME record pointing to GitHub Pages
aws route53 change-resource-record-sets \
  --profile terpedia \
  --hosted-zone-id Z1008515TFY6OXJW5Z47 \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "tersona.terpedia.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "your-username.github.io"}]
      }
    }]
  }'
```

Replace `your-username.github.io` with your actual GitHub Pages domain.

### Option B: Your Current DNS Provider

1. Log into your DNS provider (e.g., SiteGround, GoDaddy)
2. Add a **CNAME** record:
   - **Name**: `tersona`
   - **Type**: `CNAME`
   - **Value**: `your-username.github.io` (or your GitHub Pages domain)
   - **TTL**: 300 (or default)

## Step 4: Wait for DNS & SSL

1. **DNS propagation**: 5-60 minutes (sometimes up to 24 hours)
2. **GitHub SSL**: Automatically provisions after DNS resolves (usually within an hour)

Check DNS:
```bash
dig +short tersona.terpedia.com
# Should show: your-username.github.io (or CNAME target)
```

## Step 5: Verify Deployment

1. Visit `https://tersona.terpedia.com`
2. You should see the TerpeneQueen chat interface
3. Enter a Google Gemini API key to start chatting

## Troubleshooting

### Site not loading

- Check GitHub Pages status: **Settings** → **Pages** → check build status
- Verify `docs/index.html` exists and is committed
- Check Actions tab for deployment errors

### DNS not resolving

- Wait 5-60 minutes for propagation
- Verify CNAME record is correct: `dig tersona.terpedia.com CNAME`
- Ensure no conflicting A records exist

### SSL certificate issues

- GitHub provisions SSL automatically after DNS resolves
- Wait up to 1 hour after DNS is correct
- Check **Settings** → **Pages** for SSL status

### API key errors

- Users must provide their own Google Gemini API key
- Get keys at: https://aistudio.google.com/apikey
- Keys are stored in browser localStorage (not sent to your server)

## Updating the Site

1. Edit `docs/index.html` (or other files in `docs/`)
2. Commit and push to `main` branch
3. GitHub Actions will automatically deploy (see `.github/workflows/pages.yml`)

## Architecture

- **Frontend**: Single HTML file with embedded CSS/JS
- **API**: Direct calls to Google Gemini API from browser
- **Hosting**: GitHub Pages (static site)
- **Domain**: tersona.terpedia.com (CNAME to GitHub Pages)

No backend server required! All processing happens client-side.
