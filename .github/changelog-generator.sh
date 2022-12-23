#!/bin/bash
# Don't forget execute this commands first!!!
# >> chmod +x ./changelog-generator.sh

# Check the current folder is a git repository
$(git -C $PWD rev-parse)
if [[ $? != 0 ]]; then
    exit 1
fi

# Color formatting
RED="\033[0;31m"
GREEN="\033[0;32m"
RESET="\033[0m"

# Handel input parameters
if [ $? == 0 ]; then
    case "$1" in
    -h | help)
        echo "help :)"
        ;;

    -cf=*)
        CONFIG_FILE_PATH=$(cut -c 5- <<<"$1")
        ;;

    config-file=*)
        CONFIG_FILE_PATH=$(cut -c 13- <<<"$1")
        ;;

    *)
        echo $"Usage: $0 {help(-h)|config-file(-cf)}"
        exit 1
        ;;

    esac
else
    printf "\n${RED}An error occurred. Please try again.${RESET}\n"
    exit 1
fi

# TODO install pyyaml
# if [pip  list | grep -F pyyaml]; then
#     pip install pyyaml
# fi
python3 ~/changelog-generator/.github/commit-parser.py "$CONFIG_FILE_PATH"
