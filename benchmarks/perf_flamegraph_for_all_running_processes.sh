#!/bin/bash

# Usage: perf_flamegraph_for_all_running_processes.sh
# Purpose: Capture an on-CPU stack profile for the whole host and render it as a flamegraph.
#          Does not filter which PIDs to capture.
#          Stack traces will be collected from any processes running on CPU each time the sampling timer event triggers.

DURATION_SECONDS=30

# Use a temp dir.  This avoids polluting current dir and supports concurrent runs of this script.
OUTDIR=$( mktemp -d /tmp/perf-record-results.XXXXXXXX )
cd "$OUTDIR"

# Name the output files to clearly indicate the scope and timestamp of the capture.
OUTFILE_PREFIX="$( hostname -s ).$( date +%Y%m%d_%H%M%S_%Z ).all_cpus"
OUTFILE_PERF_SCRIPT="${OUTFILE_PREFIX}.perf-script.txt"
OUTFILE_FLAMEGRAPH="${OUTFILE_PREFIX}.flamegraph.svg"

# Clone the FlameGraph scripts.  (Chef should do this once per host, but for now, do it on demand.)
git clone --quiet --depth=1 https://github.com/brendangregg/FlameGraph.git
export PATH="./FlameGraph:$PATH"

# Capture timer-based profile, resolve symbols, and render as a flamegraph.
echo "Starting capture."
sudo perf record --freq 99 -g --all-cpus -- sleep "${DURATION_SECONDS}"
sudo perf script --header > "${OUTFILE_PERF_SCRIPT}"
cat "${OUTFILE_PERF_SCRIPT}" | stackcollapse-perf.pl --kernel | flamegraph.pl --hash --colors=perl > "${OUTFILE_FLAMEGRAPH}"

# Show user where the output is.
echo "Flamegraph:       ${OUTDIR}/${OUTFILE_FLAMEGRAPH}"
echo "Raw stack traces: ${OUTDIR}/${OUTFILE_PERF_SCRIPT}"
