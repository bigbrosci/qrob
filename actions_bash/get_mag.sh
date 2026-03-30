#!/usr/bin/env bash
# Simple get_mag.sh - extract magnetization block from OUTCAR
# Assumes OUTCAR and CONTCAR are well-formed.

if [ $# -lt 1 ]; then
	echo "Usage: $(basename "$0") INDEX [INDEX ...]   (use 'all' to print full block)"
	exit 1
fi

if [ ! -f OUTCAR ]; then
	echo "OUTCAR not found" >&2; exit 2
fi
if [ ! -f CONTCAR ] && [ ! -f POSCAR ]; then
	echo "CONTCAR or POSCAR not found" >&2; exit 3
fi

# find last magnetization (x) line
Nline=$(grep -n "magnetization (x)" OUTCAR | tail -n1 | cut -d: -f1)

# atom count from CONTCAR or POSCAR (line 7 typical)
POSFILE=CONTCAR
[ -f POSCAR ] && POSFILE=POSCAR
Natom=$(sed -n '7p' "$POSFILE" | awk '{s=0; for(i=1;i<=NF;i++) if($i~/^[0-9]+$/) s+= $i; } END{print s}')

Nstart=$((Nline+4))
Nend=$((Nstart+Natom-1))

TMP=$(mktemp)
sed -n "${Nstart},${Nend}p" OUTCAR > "$TMP"

if [ "$1" = "all" ]; then
	cat "$TMP"
	rm -f "$TMP"
	exit 0
fi

for idx in "$@"; do
	# print idx-th line (1-based) of the block
	sed -n "${idx}p" "$TMP"
done

rm -f "$TMP"
