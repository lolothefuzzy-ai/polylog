# CI/CD Setup Guide

## Current Status

### ✅ Configured
- **GitHub Actions**: CI workflow active (`.github/workflows/ci.yml`)
- **Codecov**: Configured in workflow (needs `CODECOV_TOKEN` secret)
- **Mergify**: Configuration file exists (`.mergify.yml`)

### ⚠️ Needs Setup

#### Codecov
1. Go to https://codecov.io
2. Sign in with GitHub
3. Add repository `lolothefuzzy-ai/polylog`
4. Copy token
5. Add to GitHub Secrets: `CODECOV_TOKEN`

#### Mergify
1. Install Mergify app: https://github.com/apps/mergify
2. Enable for repository
3. Configuration already in `.mergify.yml`

#### Slack Notifications (Optional)
1. Create Slack webhook
2. Add to GitHub Secrets: `SLACK_WEBHOOK_URL`

## Quick Fix Commands

```bash
# Test CI locally
act -j python-tests

# Check Codecov connection
curl -X GET https://codecov.io/api/gh/lolothefuzzy-ai/polylog

# Verify Mergify
gh api repos/lolothefuzzy-ai/polylog/hooks
```

## Localhost Testing Ports

- **API**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **Visual Tests**: Playwright uses frontend port automatically

