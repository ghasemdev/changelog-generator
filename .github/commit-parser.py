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


def main(args):
    with open(args[1], "r") as stream:
        try:
            configs = yaml.safe_load(stream)
            generating_range = configs["generating"]["range"]
            s = generating_range["from"]
            e = generating_range["to"]

            result = subprocess.run(
                ['git', 'log', f'{s}..{e}', '--merges', '--first-parent'], stdout=subprocess.PIPE)

            merge_commits = re.split(
                pattern, result.stdout.decode('utf-8')[7::])
            merge_commits = ["""
29fadf4c5fc46536ced49baaf2c9fc8f690cffca
Merge: de00e6b 4b31abb
Author: Ghasem Shirdel <ghasem79.dev@gmail.com>
Date:   Wed Aug 24 22:06:02 2022 +0430
            
feat(login): add new login screen
                
description
                
merge by
                
            """]
            print(datetime.today().strftime('%Y-%m-%d'))
            for merge_commit in merge_commits:
                print(merge_commit)
                print("-----------")
                merge_commit_line = merge_commit.strip().split("\n")
                commit_id = merge_commit_line[0]
                merge = merge_commit_line[1].split(": ")[1]
                author = merge_commit_line[2].split(": ")[1]
                commit_date = merge_commit_line[3].split(": ")[1].strip()
                commit = merge_commit_line[5::]
                print(
                    f"commit_id={commit_id}, merge={merge}, author={author}, commit_date={commit_date}")
                for line in commit:
                    print(line)
        except yaml.YAMLError as exc:
            print(exc)


if __name__ == '__main__':
    main(sys.argv)
