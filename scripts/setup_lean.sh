#!/usr/bin/env bash
# Build a Lean 4 environment that can typecheck conjectures.io targets locally.
#
#   bash _work/setup_lean.sh
#
# Why this shape:
#   * The subnet's pinned commit (8432eac9...) does NOT resolve on either public
#     formal-conjectures remote. Verified 2026-09-14: `git cat-file -t` against
#     conjectures-io/formal-conjectures and google-deepmind/formal-conjectures
#     both fail with "not our ref". So the pin cannot be reproduced from public
#     sources; the fork's HEAD is used instead. Its `lean-toolchain` is
#     leanprover/lean4:v4.27.0, which DOES match the subnet's pinned toolchain,
#     so the Lean semantics are the same even though the statement bytes may not be.
#   * `lake exe cache get` is the difference between ~30 minutes and most of a day.
set -euo pipefail

export PATH="$HOME/.elan/bin:$PATH"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FC="$ROOT/_research/formal-conjectures"

echo "== elan =="
elan --version

if [ ! -d "$FC/.git" ]; then
  echo "== cloning conjectures-io/formal-conjectures =="
  git clone -q https://github.com/conjectures-io/formal-conjectures.git "$FC"
fi

cd "$FC"
echo "== HEAD =="
git log --oneline -1
echo "== lean-toolchain =="
cat lean-toolchain

echo "== installing the toolchain (this downloads Lean) =="
lake --version 2>/dev/null || true
time lake exe cache get

echo "== building the target module(s) =="
for m in "$@"; do
  echo "-- building $m"
  lake build "$m" || echo "BUILD FAILED for $m"
done

echo "== DONE =="
