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

# Monday of the ISO week a date falls in (BSD date, then GNU).
week_start() {
	local d=$1 dow
	dow=$(date -j -f %F "$d" +%u 2>/dev/null || date -d "$d" +%u)
	date -j -v-$((dow - 1))d -f %F "$d" +%F 2>/dev/null ||
		date -d "$d -$((dow - 1)) days" +%F
}

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
	# The latest day already logged, so a new week starts its own file rather than
	# extending last week's. Backfilling an earlier day still appends to this one.
	last=$(awk -F, 'NR > 1 && $1 ~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/ { if ($1 > m) m = $1 } END { print m }' "$file")
	if [[ -n "$last" && "$(week_start "$day")" > "$(week_start "$last")" ]]; then
		prev="$file"
		prev_total=$(awk -F, 'NR > 1 && toupper($1) != "TOTAL" { sum += $2 } END { print sum + 0 }' "$prev")
		file="$dir/week-of-$(week_start "$day").csv"
		echo "Date,Hours,Description" >"$file"
		echo "Started new week: ${file##*/}"
		echo "ASK: was ${prev##*/} ($prev_total h) submitted? If yes, archive it so only one period stays open."
	else
		# A hand-edited file may have lost its final newline; the row must start on its own line.
		[[ -n "$(tail -c1 "$file")" ]] && echo >>"$file"
	fi
fi

[[ "$hours" == *.* ]] || hours="$hours.0"
printf '%s,%s,"%s"\n' "$day" "$hours" "$desc" >>"$file"

total=$(awk -F, 'NR > 1 && toupper($1) != "TOTAL" { sum += $2 } END { print sum + 0 }' "$file")
echo "Added to ${file##*/}: $day, $hours h, \"$desc\""
echo "Open period total: $total h"
