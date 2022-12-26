#!/usr/bin/env python3

import sys
import yaml
import subprocess
import re

from datetime import datetime
from dataclasses import dataclass

pattern = r'\ncommit '

fake_data = [
    """
    29fadf4c5fc46536ced49baaf2c9fc8f690cffca
Merge: de00e6b 4b31abb
Author: Ghasem Shirdel <ghasem79.dev@gmail.com>
Date:   Wed Aug 24 22:06:02 2022 +0430

feat(login): add new login screen

Merge branch '201-check-being-not-empty-text-fields' into 'develop-ui-compose' (!186) by sajjad.fatehi <sajjad.fatehi@partsoftware.com>
    """,
    """
    29fadf4c5fc46536ced49baaf2c9fc8f690cffdd
Merge: de00e6b 4b31abb
Author: Ghasem Shirdel <ghasem79.dev@gmail.com>
Date:   Wed Aug 24 22:06:02 2022 +0430

feat(register): add new register page

Merge branch '201-check-being-not-empty-text-fields' into 'develop-ui-compose' (!187) by sajjad.fatehi <sajjad.fatehi@partsoftware.com>
    """,
    """
    29fadf4c5fc46536ced49baaf2c9fc8f690cffcs
Merge: de00e6b 4b31abb
Author: Ghasem Shirdel <ghasem79.dev@gmail.com>
Date:   Wed Aug 24 22:06:02 2022 +0430

fix: payment bug

Merge branch '201-check-being-not-empty-text-fields' into 'develop-ui-compose' (!200) by sajjad.fatehi <sajjad.fatehi@partsoftware.com>
    """,
    """
    29fadf4c5fc46536ced49baaf2c9fc8f690cffdd
Merge: de00e6b 4b31abb
Author: Ghasem Shirdel <ghasem79.dev@gmail.com>
Date:   Wed Aug 24 22:06:02 2022 +0430

Features(ci): add new py script

Python and shell script

Merge branch '201-check-being-not-empty-text-fields' into 'develop-ui-compose' (!189) by sajjad.fatehi <sajjad.fatehi@partsoftware.com>
    """,
]


@dataclass
class CommitInfo:
    commit_id: str
    commit_date: str
    scope: str
    title: str
    descriptions: list
    PR_author: str
    PR_link: str

# VERSIONS=$(git tag --sort=taggerdate | grep -E '^[0-9]+.[0-9]+.[0-9]+$' | tail -2)

# START_TAG=$(cut -d$'\n' -f1 <<<"$VERSIONS")
# END_TAG=$(cut -d$'\n' -f2 <<<"$VERSIONS") # can be empty in first tag

# echo "Generate CHANGELOG.md for $START_TAG..$END_TAG"

# TAIL=$(git rev-list --max-parents=0 HEAD)
# START_TAG=$TAIL
# END_TAG=HEAD
# MERGE_COMMITS=$(git log "$START_TAG".."$END_TAG" --merges --first-parent) # can be empty, or without changelog tag


def init_configs(config_file_path: str):
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
            generating_version = generating.get(
                "version")if generating != None else None
            generating_date = generating.get(
                "date")if generating != None else None
            generating_PR_link_enabled = generating.get(
                "PR_link_enabled")if generating != None else None
            generating_PR_author_enabled = generating.get(
                "PR_author_enabled")if generating != None else None
            generating_range = generating.get(
                "range") if generating != None else None
            generating_range_mode = generating_range.get(
                "mode") if generating_range != None else None
            generating_range_regex = generating_range.get(
                "regex") if generating_range != None else None
            generating_range_from = generating_range.get(
                "from") if generating_range != None else None
            generating_range_to = generating_range.get(
                "to") if generating_range != None else None

            output = configs.get("output")
            output_enabled = output.get("enabled")if output != None else None
            output_path = output.get("path")if output != None else None
            output_branch = output.get("branch")if output != None else None
            output_commit_message = output.get(
                "commit_message")if output != None else None

            trailer = configs.get("trailer")
            trailer_enabled = trailer.get(
                "enabled")if trailer != None else None
            trailer_tag = trailer.get("tag")if trailer != None else None

            categories_map = configs.get("categories")
        except yaml.YAMLError as _:
            print("Config file not found, We use default configs.")


def commit_parser(merge_commit) -> CommitInfo:
    merge_commit_line = merge_commit.strip().split("\n")
    commit_id = merge_commit_line[0]
    author = merge_commit_line[2].split(": ")[1]
    commit_date = merge_commit_line[3].split(": ")[1].strip()
    commit = list(filter(None,  merge_commit_line[5::]))

    scope = "unknown"
    if (trailer_enabled == "false" or trailer_enabled == None):
        pair = commit[0].split(":")
        if len(pair) < 2:
            title = commit[0]
        else:
            scope = re.split("\(|\)", pair[0].strip())[0]
            title = pair[1].strip()
    elif trailer_enabled == "true":
        title = commit[0]

    merge_branch = commit[-1]
    PR_link_regex = re.compile(r"(!\d*)")
    PR_link = PR_link_regex.search(merge_branch).group()

    descriptions = []
    if (len(commit) > 2):
        descriptions = commit[1:-1:]
        if trailer_enabled == "true":
            if trailer_tag == None:
                tag = "changelog"
            else:
                tag = trailer_tag

            r = re.compile(f'{tag}:')
            for description in descriptions:
                if (r.match(description)):
                    scope = description.split(":")[1].strip()
                    descriptions.remove(description)

    return CommitInfo(commit_id=commit_id, commit_date=commit_date, scope=scope,
                      title=title, descriptions=descriptions, PR_author=author, PR_link=PR_link)


def main(args):
    init_configs(args[1])
    result = subprocess.run(
        ['git', 'log', f'{generating_range_from}..{generating_range_to}', '--merges', '--first-parent'], stdout=subprocess.PIPE)
    merge_commits = re.split(pattern, result.stdout.decode('utf-8')[7::])
    merge_commits = fake_data
    print(datetime.today().strftime('%Y-%m-%d'))

    changelog_group = {}
    for merge_commit in merge_commits:
        commit = commit_parser(merge_commit)
        if changelog_group.get(commit.scope) == None:
            changelog_group[commit.scope] = [commit]
        else:
            changelog_group[commit.scope] = changelog_group[commit.scope] + [commit]

    if categories_map != None:
        new_changelog_group = {}
        for key, value in changelog_group.items():
            new_changelog_group[categories_map[key] if categories_map.get(key) != None else key] = value
        print(new_changelog_group)    
    else:
        print(changelog_group)


if __name__ == '__main__':
    main(sys.argv)
