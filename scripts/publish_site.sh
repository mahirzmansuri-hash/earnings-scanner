#!/bin/zsh
# Publish site/ to the gh-pages branch (GitHub Pages serves it).
# Run from the repo root after `python -m src.web.build`. Overwrites the branch each time.
set -euo pipefail
REMOTE=${PUBLISH_REMOTE:-$(git remote get-url origin)}  # CI passes a token URL
TMP=$(mktemp -d)
cp -R site/. "$TMP"
touch "$TMP/.nojekyll"   # tell GitHub not to run Jekyll on these files
cd "$TMP"
git init -q -b gh-pages
git add -A
git -c user.name="$(git -C "$OLDPWD" config user.name)" -c user.email="$(git -C "$OLDPWD" config user.email)" \
    commit -q -m "Publish Faultline site $(date +%Y-%m-%d)"
git push -q -f "$REMOTE" gh-pages
echo "Published $(git ls-files | wc -l | tr -d ' ') files to gh-pages"
rm -rf "$TMP"
