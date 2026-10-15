#!/bin/bash
# Append a row to a client's open timesheet CSV, then print the open period's total.
# Usage: add_entry.sh <client-dir> <hours> <description> [YYYY-MM-DD]
set -euo pipefail

dir="${1%/}"
hours="$2"
desc="$3"
day="${4:-$(date +%F)}"

if [[ ! "$hours" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
	echo "Hours must be a number, got: $hours" >&2
	exit 1
fi
if [[ "$desc" == *'"'* ]]; then
	echo "Description can't contain double quotes" >&2
	exit 1
fi
# Round-tripping through date rejects impossible dates like 2026-02-30 (BSD date, then GNU).
if [[ "$(date -j -f %F "$day" +%F 2>/dev/null || date -d "$day" +%F 2>/dev/null)" != "$day" ]]; then
	echo "Date must be a valid YYYY-MM-DD, got: $day" >&2
	exit 1
fi

shopt -s nullglob
open=("$dir"/week-of-*.csv)

if ((${#open[@]} > 1)); then
	echo "More than one open timesheet; ask which period these hours belong to:" >&2
	printf '  %s\n' "${open[@]##*/}" >&2
	exit 2
fi

if ((${#open[@]} == 0)); then
	file="$dir/week-of-$day.csv"
	echo "Date,Hours,Description" >"$file"
	echo "Started new period: ${file##*/}"
else
	file="${open[0]}"
	# A hand-edited file may have lost its final newline; the row must start on its own line.
	[[ -n "$(tail -c1 "$file")" ]] && echo >>"$file"
fi

[[ "$hours" == *.* ]] || hours="$hours.0"
printf '%s,%s,"%s"\n' "$day" "$hours" "$desc" >>"$file"

total=$(awk -F, 'NR > 1 && toupper($1) != "TOTAL" { sum += $2 } END { print sum + 0 }' "$file")
echo "Added to ${file##*/}: $day, $hours h, \"$desc\""
echo "Open period total: $total h"
