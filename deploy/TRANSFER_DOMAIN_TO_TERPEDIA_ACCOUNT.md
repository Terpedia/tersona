# Transfer terpedia.com Registration Between AWS Accounts

## Quick Decision

**Do you really need to transfer?**
- ❌ Transfer: 5-7 days, costs $12-15, complex process
- ✅ Update nameservers: 2 minutes, free, achieves same result

**Recommendation**: Just update nameservers in the syzygyx account to point to the terpedia Route53 hosted zone. This is what 99% of people do.

## If You Still Want to Transfer

### Step 1: Prepare Source Account (syzygyx - 204181352839)

1. Log into AWS Console with syzygyx account
2. Go to Route 53 → Registered domains → terpedia.com
3. Disable **Transfer lock** (if enabled)
4. Disable **Auto-renew** (optional, but recommended during transfer)
5. Get **Authorization code** (EPP code) - click "Get authorization code"
6. Note down the authorization code

### Step 2: Initiate Transfer in Destination Account (terpedia - 419453210961)

1. Log into AWS Console with terpedia account
2. Go to Route 53 → Registered domains
3. Click **Transfer domain**
4. Enter domain: `terpedia.com`
5. Select **Transfer from another AWS account**
6. Enter the **source AWS account ID**: `204181352839`
7. Enter the **authorization code** from Step 1
8. Complete payment ($12-15 for .com transfer + 1 year renewal)
9. Confirm transfer

### Step 3: Accept Transfer in Source Account

1. Log back into syzygyx account
2. Go to Route 53 → Registered domains → Requests
3. Find the transfer request
4. Click **Accept transfer**

### Step 4: Wait

- Transfer takes 5-7 days to complete
- You'll receive email notifications
- Domain remains functional during transfer

## Alternative: Just Update Nameservers (RECOMMENDED)

Instead of transferring, update nameservers in syzygyx account:

1. Log into syzygyx AWS Console
2. Go to Route 53 → Registered domains → terpedia.com
3. Click **Add or edit name servers**
4. Update to:
   ```
   ns-1847.awsdns-38.co.uk
   ns-1031.awsdns-00.org
   ns-50.awsdns-06.com
   ns-811.awsdns-37.net
   ```
5. Click **Update**
6. Wait 5-60 minutes

**Result**: DNS managed in terpedia account, domain registered in syzygyx account. This is perfectly fine and how most organizations operate.

## Cost Comparison

| Option | Time | Cost | Complexity |
|--------|------|------|------------|
| Update nameservers | 5 min + propagation | $0 | Easy |
| Transfer registration | 5-7 days | $12-15 | Medium |

## Why Update Nameservers is Better

- ✅ Instant (5-60 min propagation)
- ✅ Free
- ✅ No downtime risk
- ✅ Reversible instantly
- ✅ Achieves same DNS management goal
- ✅ Industry standard practice

## When to Actually Transfer

Only transfer if:
- You're consolidating billing
- You're closing the syzygyx AWS account
- You need domain registration and DNS in same account for compliance

Otherwise, just update nameservers!
