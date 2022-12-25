#!/usr/bin/env python3

import sys
import yaml
import subprocess
import re

from datetime import datetime

pattern = r'\ncommit '

# VERSIONS=$(git tag --sort=taggerdate | grep -E '^[0-9]+.[0-9]+.[0-9]+$' | tail -2)

# START_TAG=$(cut -d$'\n' -f1 <<<"$VERSIONS")
# END_TAG=$(cut -d$'\n' -f2 <<<"$VERSIONS") # can be empty in first tag

# echo "Generate CHANGELOG.md for $START_TAG..$END_TAG"

# TAIL=$(git rev-list --max-parents=0 HEAD)
# START_TAG=$TAIL
# END_TAG=HEAD
# MERGE_COMMITS=$(git log "$START_TAG".."$END_TAG" --merges --first-parent) # can be empty, or without changelog tag


def init_configs(config_file_path):
    global generating_range_mode
    global generating_range_regex
    global generating_range_from
    global generating_range_to
    global generating_version
    global generating_date
    global generating_PR_link_enabled
    global generating_PR_author_enabled

    global output_enabled
    global output_path
    global output_branch
    global output_commit_message

    global trailer_enabled
    global trailer_tag

    global categories_map

    with open(config_file_path, "r") as stream:
        try:
            configs = yaml.safe_load(stream)
            generating = configs.get("generating")
            generating_range = generating.get("range")
            generating_range_mode = generating_range.get("mode")
            generating_range_regex = generating_range.get("regex")
            generating_range_from = generating_range.get("from")
            generating_range_to = generating_range.get("to")
            generating_version = generating.get("version")
            generating_date = generating.get("date")
            generating_PR_link_enabled = generating.get("PR_link_enabled")
            generating_PR_author_enabled = generating.get("PR_author_enabled")

            output = configs.get("output")
            output_enabled = output.get("enabled")
            output_path = output.get("path")
            output_branch = output.get("branch")
            output_commit_message = output.get("commit_message")

            trailer = configs.get("trailer")
            trailer_enabled = trailer.get("enabled")
            trailer_tag = trailer.get("tag")

            categories_map = configs.get("categories")
        except yaml.YAMLError as _:
            print("Config file not found, We use default configs.")


def main(args):
    init_configs(args[1])
    result = subprocess.run(
        ['git', 'log', f'{generating_range_from}..{generating_range_to}', '--merges', '--first-parent'], stdout=subprocess.PIPE)
    merge_commits = re.split(pattern, result.stdout.decode('utf-8')[7::])
    merge_commits = ["""
29fadf4c5fc46536ced49baaf2c9fc8f690cffca
Merge: de00e6b 4b31abb
Author: Ghasem Shirdel <ghasem79.dev@gmail.com>
Date:   Wed Aug 24 22:06:02 2022 +0430

feat(login): add new login screen

This is a decription

changelog: feat

Merge branch '201-check-being-not-empty-text-fields' into 'develop-ui-compose' (!186) by sajjad.fatehi <sajjad.fatehi@partsoftware.com>"""]
    print(datetime.today().strftime('%Y-%m-%d'))
    for merge_commit in merge_commits:
        merge_commit_line = merge_commit.strip().split("\n")
        commit_id = merge_commit_line[0]
        merge = merge_commit_line[1].split(": ")[1]
        author = merge_commit_line[2].split(": ")[1]
        commit_date = merge_commit_line[3].split(": ")[1].strip()
        commit = list(filter(None,  merge_commit_line[5::]))
        title = commit[0]
        merge_branch = commit[-1]
        PR_link_regex = re.compile(r"(!\d*)")
        PR_link = PR_link_regex.search(merge_branch).group()
        if (len(commit) > 2):
            descriptons = commit[1:-1:]
            r = re.compile('changelog:')
            for descripton in descriptons:
                if (r.match(descripton)):
                    trailer = descripton.split(":")[1].strip()
                    descriptons.remove(descripton)
        print(commit_id,merge,author,commit_date,title,PR_link,trailer)


if __name__ == '__main__':
    main(sys.argv)
