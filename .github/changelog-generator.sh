#!/bin/bash
# Don't forget execute this commands first!!!
# >> chmod +x ./changelog-generator.sh

# Check the current folder is a git repository
if ! git -C "$PWD" rev-parse; then
  exit 1
fi

# Color formatting
RED="\e[31m"
GREEN="\e[32m"
RESET="\e[0m"

# Handel input parameters
case "$1" in
-h | help)
  printf "${GREEN}%s${RESET}\n" "help :)"
  exit 0
  ;;

-cf=*)
  CONFIG_FILE_PATH=$(cut -c 5- <<<"$1")
  ;;

config-file=*)
  CONFIG_FILE_PATH=$(cut -c 13- <<<"$1")
  ;;

*)
  printf "${RED}Usage: %s {help(-h)|config-file(-cf)}${RESET}\n" "$0"
  exit 1
  ;;

esac

if pip list | grep -F pyyaml; then
  pip install pyyaml
fi
python3 configs/changelog/commit-parser.py "$CONFIG_FILE_PATH"
