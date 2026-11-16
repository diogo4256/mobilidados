#!/bin/bash
# Render a case's dossier.md to dossier.pdf, a standalone A4 document. Usage: scripts/dossier/build.sh cases/<case>
# Needs pandoc and Node with Playwright (see pdf.js). Run `mobilidados dossier cases/<case>` first if the ledger changed.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
case_dir=$(cd "$1" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
title=$(sed -n 's/^# //p' "$case_dir/dossier.md" | head -1)
(cd "$case_dir" && pandoc dossier.md -f gfm -t html5 -s --metadata pagetitle="$title" --css "$here/dossier.css" -o "$tmp/dossier.html")
sed -i "s|src=\"results/|src=\"$case_dir/results/|g" "$tmp/dossier.html"  # the figures, embedded in the PDF
node "$here/pdf.js" "$tmp/dossier.html" "$case_dir/dossier.pdf" "$title · dossier técnico a partir de dados públicos"
echo "wrote $case_dir/dossier.pdf"
