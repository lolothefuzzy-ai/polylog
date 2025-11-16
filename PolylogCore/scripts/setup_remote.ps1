# Run this script after creating the remote repository on GitHub
# Replace YOUR-REPOSITORY-URL with your actual repository URL

Set-ExecutionPolicy Bypass -Scope Process -Force
git remote set-url origin https://github.com/lolothefuzzy-ai/polylog.git
git push -u origin main
