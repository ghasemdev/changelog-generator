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

help(){
  printf "${GREEN}%s${RESET}\n" "These are common changelog-generator commands used in various situations:


      [config-file=<PATH>] [-cf=<PATH>]    Config file path
      [version=<SEMANTIC_VERSIONING>] [-v=<SEMANTIC_VERSIONING>]    Changelog version(Optional)
"
}

CHANGELOG_VERSION="null"

# Handel input parameters
case "$1" in
-h | help)
  help
  exit 0
  ;;

-cf=*)
  CONFIG_FILE_PATH=$(cut -c 5- <<<"$1")

  case "$2" in

  -v=*)
    CHANGELOG_VERSION=$(cut -c 4- <<<"$2")
    ;;

  -version=*)
    CHANGELOG_VERSION=$(cut -c 10- <<<"$2")
    ;;

  esac
  ;;

config-file=*)
  CONFIG_FILE_PATH=$(cut -c 13- <<<"$1")

  case "$2" in

  -v=*)
    CHANGELOG_VERSION=$(cut -c 4- <<<"$2")
    ;;

  -version=*)
    CHANGELOG_VERSION=$(cut -c 10- <<<"$2")
    ;;

  esac
  ;;

-v=*)
  CHANGELOG_VERSION=$(cut -c 4- <<<"$1")

  case "$2" in

  -cf=*)
    CONFIG_FILE_PATH=$(cut -c 5- <<<"$2")
    ;;

  config-file=*)
    CONFIG_FILE_PATH=$(cut -c 13- <<<"$2")
    ;;

  esac
  ;;

-version=*)
  CHANGELOG_VERSION=$(cut -c 10- <<<"$1")

  case "$2" in

  -cf=*)
    CONFIG_FILE_PATH=$(cut -c 5- <<<"$2")
    ;;

  config-file=*)
    CONFIG_FILE_PATH=$(cut -c 13- <<<"$2")
    ;;

  esac
  ;;

*)
  printf "${RED}usage: %s [help(-h)] [config-file(-cf)=<PATH>]${RESET}\n" "$0"
  exit 1
  ;;

esac

if pip list | grep -F pyyaml; then
  pip install pyyaml
fi
python3 configs/changelog/commit-parser.py "$CONFIG_FILE_PATH" "$CHANGELOG_VERSION"
