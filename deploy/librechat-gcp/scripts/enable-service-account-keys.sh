#!/usr/bin/env bash
# Disable the organization policy that blocks service account key creation
# The policy is set at the organization level

set -e

ORG_ID="884764836064"
PROJECT_ID="terpedia-489015"

echo "Your organization ID: $ORG_ID"
echo "Your project ID: $PROJECT_ID"
echo ""

echo "Checking organization policy at org level..."
gcloud org-policies describe \
  constraints/iam.disableServiceAccountKeyCreation \
  --organization="$ORG_ID" 2>&1 || echo "Policy may not be explicitly set at org level"

echo ""
echo "⚠️  This policy is enforced at the ORGANIZATION level."
echo ""
echo "To disable it, you need:"
echo "  1. Organization Policy Administrator role on the organization"
echo "  2. Run this command:"
echo ""
echo "     gcloud org-policies delete \\"
echo "       constraints/iam.disableServiceAccountKeyCreation \\"
echo "       --organization=$ORG_ID"
echo ""
echo "Or contact your organization admin to:"
echo "  - Disable the constraint at org level, OR"
echo "  - Create an exception for project $PROJECT_ID"
echo ""
echo "Alternative: Use Workload Identity Federation instead of service account keys"
echo "See: https://cloud.google.com/iam/docs/workload-identity-federation"
