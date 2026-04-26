#!/usr/bin/env bash

# Input: optional output file path as the first argument.
# Output: diagnostic report printed to stdout and optionally written to a file.
# Purpose: collect the cluster-side environment details needed to choose a compatible local stack.

# Usage:
# bash Task1/src/diagnose_cluster.sh
# Save output to a file:
# bash Task1/src/diagnose_cluster.sh cluster_probe.txt
# Help: 
# bash Task1/src/diagnose_cluster.sh --help


set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./diagnose_cluster.sh [output-file]

If an output file is provided, the full probe report is also saved there.
EOF
}

section() {
  local title="$1"
  printf '\n=== %s ===\n' "$title"
}

has_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1
}

run_optional() {
  # Input: shell command tokens.
  # Output: command output when available; otherwise a short not-available message.
  # Purpose: keep the script informative without aborting on missing cluster tools.
  if "$@"; then
    return 0
  fi
  printf 'not available or command failed: %s\n' "$*"
}

probe_host() {
  section "host"
  hostname || true
  whoami || true
  pwd || true
  uname -a || true
  run_optional date
  run_optional bash --version
  if has_command cat; then
    run_optional cat /etc/os-release
  else
    printf 'not available: cat /etc/os-release\n'
  fi
}

probe_limits() {
  section "shell limits"
  ulimit -a || true

  section "local resources"
  if has_command nproc; then
    run_optional nproc
  elif has_command sysctl; then
    run_optional sysctl -n hw.ncpu
  else
    printf 'cpu count command not available\n'
  fi

  if has_command free; then
    run_optional free -h
  elif has_command vm_stat; then
    run_optional vm_stat
  else
    printf 'memory inspection command not available\n'
  fi

  run_optional df -h
  if has_command quota; then
    run_optional quota -s
  else
    printf 'quota command not available\n'
  fi
}

probe_python() {
  section "python"
  if has_command python3; then
    run_optional command -v python3
    run_optional python3 --version
    run_optional python3 -c 'import sys, platform; print(sys.executable); print(sys.version); print(platform.platform())'
    run_optional python3 -m pip --version
    run_optional python3 -m pip list
    run_optional python3 -c 'import mrjob; print(mrjob.__version__)'
  else
    printf 'python3 not available\n'
  fi

  if has_command python; then
    run_optional command -v python
    run_optional python --version
  else
    printf 'python not available\n'
  fi
}

probe_java() {
  section "java"
  if has_command java; then
    run_optional command -v java
    run_optional java -version
  else
    printf 'java not available\n'
  fi
  printf 'JAVA_HOME=%s\n' "${JAVA_HOME:-}"
}

probe_hadoop() {
  section "hadoop"
  if has_command hadoop; then
    run_optional command -v hadoop
    run_optional hadoop version
    run_optional hadoop classpath --glob
  else
    printf 'hadoop not available\n'
  fi

  section "hdfs"
  if has_command hdfs; then
    run_optional command -v hdfs
    run_optional hdfs version
    run_optional hdfs getconf -confKey fs.defaultFS
    run_optional hdfs getconf -confKey dfs.blocksize
    run_optional hdfs getconf -confKey dfs.replication
    run_optional hdfs dfs -ls /
    run_optional hdfs dfs -ls /dic_shared
    run_optional hdfs dfs -ls /dic_shared/amazon-reviews/full
    run_optional hdfs dfs -du -h /dic_shared/amazon-reviews/full/reviewscombined.json
    run_optional hdfs dfs -du -h /dic_shared/amazon-reviews/full/reviews_devset.json
  else
    printf 'hdfs not available\n'
  fi

  section "yarn"
  if has_command yarn; then
    run_optional command -v yarn
    run_optional yarn version
    run_optional yarn node -list
    run_optional yarn application -list
    run_optional yarn queue -list
    run_optional yarn queue -status default
  else
    printf 'yarn not available\n'
  fi

  section "mapreduce defaults"
  if has_command hdfs; then
    run_optional hdfs getconf -confKey yarn.nodemanager.resource.memory-mb
    run_optional hdfs getconf -confKey yarn.scheduler.minimum-allocation-mb
    run_optional hdfs getconf -confKey yarn.scheduler.maximum-allocation-mb
    run_optional hdfs getconf -confKey mapreduce.map.memory.mb
    run_optional hdfs getconf -confKey mapreduce.reduce.memory.mb
    run_optional hdfs getconf -confKey mapreduce.map.java.opts
    run_optional hdfs getconf -confKey mapreduce.reduce.java.opts
    run_optional hdfs getconf -confKey mapreduce.job.reduces
  else
    printf 'mapreduce config probes unavailable because hdfs is missing\n'
  fi

  section "environment"
  env | sort | egrep '^(HADOOP|HDFS|YARN|JAVA|PYTHON|PATH|LD_LIBRARY_PATH)=' || true
}

write_report() {
  # Input: optional output file path.
  # Output: complete diagnostics stream to stdout and optional file.
  # Purpose: centralize report generation and optional persistence.
  local output_file="${1:-}"

  if [[ -n "$output_file" ]]; then
    {
      probe_host
      probe_limits
      probe_python
      probe_java
      probe_hadoop
    } | tee "$output_file"
    return 0
  fi

  probe_host
  probe_limits
  probe_python
  probe_java
  probe_hadoop
}

main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    return 0
  fi

  write_report "${1:-}"
}

main "$@"