#!/usr/bin/env bash
# Fetch everything this guide is built from.
#
#   ./scripts/sync_pool.sh
#
# Two things are pulled, and they are different kinds of thing:
#
#   1. THE LIVE CATALOG -- GET /v1/catalog/conjectures on the running validator.
#      Unauthenticated. This is the authority on what is currently offered and what
#      each target is currently quoted at. It changes; re-run before you act.
#
#   2. THE PINNED TASK POOL -- the conjectures-io git repositories. These are the
#      exact bytes a submission is checked against, plus the audit log that says
#      which targets left the pool and why.
#
# Nothing here needs a wallet, a key, or an account.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESEARCH="$ROOT/_research"
DATA="$ROOT/data"
API="${CONJECTURES_API:-https://conjectures.io}"

mkdir -p "$RESEARCH" "$DATA"

echo "==> live catalog from $API"
python3 - "$API" "$DATA/catalog_live.json" <<'PY'
import json, sys, time, urllib.request

api, out = sys.argv[1], sys.argv[2]
items, offset, total = [], 0, None
while True:
    url = f"{api}/v1/catalog/conjectures?limit=100&offset={offset}"
    req = urllib.request.Request(url, headers={"accept": "application/json",
                                               "user-agent": "conjectures-guide/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        page = json.load(resp)
    total = page.get("total")
    batch = page.get("items", [])
    items.extend(batch)
    print(f"    offset {offset:>4}  +{len(batch):<3}  cumulative {len(items)}/{total}")
    if len(batch) < 100:
        break
    offset += 100
    time.sleep(0.4)

with open(out, "w", encoding="utf-8") as fh:
    json.dump(items, fh, indent=1, ensure_ascii=False)
print(f"    wrote {len(items)} targets -> {out}")
PY

echo "==> pool metadata from $API"
curl -fsS --max-time 30 "$API/v1/catalog/meta" -o "$DATA/catalog_meta.json"
echo "    wrote $DATA/catalog_meta.json"

for repo in conjectures-tasks conjectures-validator conjectures-miner conjectures-contribution; do
    dir="$RESEARCH/$repo"
    if [ -d "$dir/.git" ]; then
        echo "==> updating $repo"
        git -C "$dir" fetch --depth 1 origin >/dev/null 2>&1 || true
        git -C "$dir" reset --hard origin/HEAD >/dev/null 2>&1 || git -C "$dir" pull --ff-only -q || true
    else
        echo "==> cloning $repo"
        git clone --depth 1 -q "https://github.com/conjectures-io/$repo.git" "$dir"
    fi
    printf '    %s @ %s\n' "$repo" "$(git -C "$dir" rev-parse --short HEAD)"
done

# The upstream formalization repository the pool is drawn from, pinned by the
# validator. Only needed if you intend to check statements against the source of
# truth rather than against the bundles; it is large.
if [ "${WITH_UPSTREAM:-0}" = "1" ]; then
    echo "==> cloning google-deepmind/formal-conjectures (this is large)"
    dir="$RESEARCH/formal-conjectures"
    [ -d "$dir/.git" ] || git clone --depth 1 -q \
        https://github.com/google-deepmind/formal-conjectures.git "$dir"
fi

echo
echo "==> building the catalog"
python3 "$ROOT/scripts/build_catalog.py" --out "$DATA"
