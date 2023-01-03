#!/usr/bin/env python3

import sys
import yaml
import subprocess
import re

from datetime import datetime
from dataclasses import dataclass
from os.path import exists as file_exists

pattern = r'\ncommit '


@dataclass
class CommitInfo:
    commit_id: str
    commit_date: str
    scope: str
    title: str
    descriptions: list
    PR_author: str
    PR_link: str


def init_configs(config_file_path: str):
    global generating_range_mode
    global generating_range_regex
    global generating_range_from
    global generating_range_to
    global generating_version
    global generating_date
    global generating_PR_link_enabled
    global generating_PR_path
    global generating_PR_author_enabled

    global output_file_enabled
    global output_file_path
    global output_file_branch
    global output_file_commit_message
    global output_file_delimiter

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
                "PR_link_enabled")if generating != None else "true"
            generating_PR_path = generating.get(
                "PR_path")if generating != None else None
            generating_PR_author_enabled = generating.get(
                "PR_author_enabled")if generating != None else "false"
            generating_range = generating.get(
                "range") if generating != None else None
            generating_range_mode = generating_range.get(
                "mode") if generating_range != None else "two_last"
            generating_range_regex = generating_range.get(
                "regex") if generating_range != None else "^[0-9]+.[0-9]+.[0-9]+$"
            generating_range_from = generating_range.get(
                "from") if generating_range != None else None
            generating_range_to = generating_range.get(
                "to") if generating_range != None else None

            output_file = configs.get("output_file")
            output_file_enabled = output_file.get(
                "enabled")if output_file != None else "false"
            output_file_path = output_file.get(
                "path")if output_file != None else "./CHANGELOG.md"
            output_file_branch = output_file.get(
                "branch")if output_file != None else "master"
            output_file_commit_message = output_file.get(
                "commit_message")if output_file != None else "Update CHANGELOG.md"
            output_file_delimiter = output_file.get(
                "delimiter")if output_file != None else "---"

            trailer = configs.get("trailer")
            trailer_enabled = trailer.get(
                "enabled")if trailer != None else "false"
            trailer_tag = trailer.get("tag")if trailer != None else "changelog"

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
    else:
        raise ValueError("Unknown `trailer_enabled` in config file!!")

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


def generate_changelog(changelog_group: dict, changelog_version: str) -> str:
    current_date = datetime.today().strftime('%Y-%m-%d')
    date = current_date if generating_date == None else generating_date

    if generating_version == None:
        if changelog_version == "null":
            raise ValueError("`generating_version` required in config file!!")
        else:
            version = changelog_version
    else:
        version = generating_version

    changelog = ""
    changelog_group_len = len(changelog_group.keys())
    changelog_group_counter = 0
    for scope, commits in changelog_group.items():
        changelog += f"### {scope}\n\n"

        commits_len = len(commits)
        commit_counter = 0
        for commit in commits:
            # Add PR link
            if (generating_PR_link_enabled == "false" or generating_PR_link_enabled == None):
                changelog += f"- {commit.title}"
            elif (generating_PR_link_enabled == "true"):
                if generating_PR_path != None:
                    changelog += f"- [{commit.title}]({generating_PR_path}{commit.PR_link})"
                else:
                    raise ValueError(
                        "When `PR_link_enabled` is true you should provide a `PR_path`!!")
            else:
                raise ValueError(
                    "Unknown `generating_PR_link_enabled` in config file!!")

            # Add PR author
            if (generating_PR_author_enabled != None and generating_PR_author_enabled == "true"):
                changelog += f" by {commit.PR_author}"

            if commit_counter < commits_len-1:
                changelog += "\n"
            commit_counter += 1

        if changelog_group_counter < changelog_group_len-1:
            changelog += "\n"
        changelog_group_counter += 1

    return f"""
## {version} ({date})

{changelog}
"""


def get_merge_commits_from_git() -> str:
    if generating_range_mode == None:
        raise ValueError("`generating_range_mode` required in config file!!")

    elif generating_range_mode == "custom":
        if generating_range_from == None or generating_range_to == None:
            raise ValueError(
                "`generating_range_from` and `generating_range_to` required in config file!!")
        else:
            code, result = subprocess.getstatusoutput(
                f'git log {generating_range_from}..{generating_range_to} --merges --first-parent')

            if code != 0:
                print(
                    f"ambiguous argument '{generating_range_from}..{generating_range_to}': unknown revision or path not in the working tree.")
                exit(1)

            if result.strip() == "":
                print("Nothing Changed!!")
                exit(0)

            print(
                f"Generate CHANGELOG.md for {generating_range_from}..{generating_range_to}")

    elif generating_range_mode == "two_last":
        if generating_range_regex == None:
            raise ValueError(
                "`generating_range_regex` required in config file!!")
        else:
            code, versions = subprocess.getstatusoutput(
                f'git tag --sort=taggerdate | grep -E {generating_range_regex} | tail -2')

            if code != 0:
                print(f"Unknown error!")
                exit(1)

            tags = versions.split("\n")

            if len(tags) < 2:
                print("At least two tag required!!")
                exit(1)

            code, result = subprocess.getstatusoutput(
                f'git log {tags[0]}..{tags[1]} --merges --first-parent')

            if code != 0:
                print(
                    f"ambiguous argument '{tags[0]}..{tags[1]}': unknown revision or path not in the working tree.")
                exit(1)

            if result.strip() == "":
                print("Nothing Changed!!")
                exit(0)

            print(f"Generate CHANGELOG.md for {tags[0]}..{tags[1]}")

    elif generating_range_mode == "last_head":
        if generating_range_regex == None:
            raise ValueError(
                "`generating_range_regex` required in config file!!")
        else:
            code, last_version = subprocess.getstatusoutput(
                f'git tag --sort=taggerdate | grep -E {generating_range_regex} | tail -1')

            if code != 0:
                print(f"Unknown error!")
                exit(1)

            if last_version.strip() == "":
                print("There is no tag!!")
                exit(1)

            code, result = subprocess.getstatusoutput(
                f'git log {last_version}..HEAD --merges --first-parent')

            if code != 0:
                print(
                    f"ambiguous argument '{last_version}..HEAD': unknown revision or path not in the working tree.")
                exit(1)

            if result.strip() == "":
                print("Nothing Changed!!")
                exit(0)

            print(f"Generate CHANGELOG.md for {last_version}..HEAD")

    elif generating_range_mode == "tail_last":
        if generating_range_regex == None:
            raise ValueError(
                "`generating_range_regex` required in config file!!")
        else:
            code, tail = subprocess.getstatusoutput(
                'git rev-list --max-parents=0 HEAD')

            if code != 0:
                print(f"Unknown error!")
                exit(1)

            code, last_version = subprocess.getstatusoutput(
                f'git tag --sort=taggerdate | grep -E {generating_range_regex} | tail -1')

            if code != 0:
                print(f"Unknown error!")
                exit(1)

            if last_version.strip() == "":
                print("There is no tag!!")
                exit(1)

            code, result = subprocess.getstatusoutput(
                f'git log {tail}..{last_version} --merges --first-parent')

            if code != 0:
                print(
                    f"ambiguous argument 'TAIL..{last_version}': unknown revision or path not in the working tree.")
                exit(1)

            if result.strip() == "":
                print("Nothing Changed!!")
                exit(0)

            print(f"Generate CHANGELOG.md for TAIL..{last_version}")

    elif generating_range_mode == "tail_head":
        code, tail = subprocess.getstatusoutput(
            'git rev-list --max-parents=0 HEAD')

        if code != 0:
            print(f"Unknown error!")
            exit(1)

        code, result = subprocess.getstatusoutput(
            f'git log {tail}..HEAD --merges --first-parent')

        if code != 0:
            print(
                f"ambiguous argument 'TAIL..HEAD': unknown revision or path not in the working tree.")
            exit(1)

        if result.strip() == "":
            print("Nothing Changed!!")
            exit(0)

        print(f"Generate CHANGELOG.md for TAIL..HEAD")

    else:
        raise ValueError("`generating_range_mode` is unknown!!")
    return result


def generate_changelog_file(changelog_message: str):
    if output_file_path != None:
        if file_exists(output_file_path):
            changelog_version = changelog_message.strip().split("\n")[0]

            with open(output_file_path, "r") as changelog_file:
                temp = list(map(lambda x: x.strip(),
                            changelog_file.readlines()))

                if changelog_version in temp:
                    print("This changelog version already exist!!")
                else:
                    header_index = temp.index(output_file_delimiter) + 1
                    temp.insert(header_index, changelog_message)
                    with open(output_file_path, "w") as changelog_file:
                        changelog_file.write('\n'.join(temp))

        else:
            with open(output_file_path, "w") as changelog_file:
                changelog_file.write("""
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

---

            """)
                changelog_file.write(changelog_message)

    else:
        raise ValueError("`output_file_path` is required in config file!!")


def main(args):
    init_configs(args[1])

    merge_commits = re.split(pattern, get_merge_commits_from_git()[7::])

    # Create dict from commit scope
    changelog_group = {}
    for merge_commit in merge_commits:
        commit = commit_parser(merge_commit)
        if changelog_group.get(commit.scope) == None:
            changelog_group[commit.scope] = [commit]
        else:
            changelog_group[commit.scope] = changelog_group[commit.scope] + [commit]

    # Mapped commit scopes
    if categories_map != None:
        new_changelog_group = {}
        for key, value in changelog_group.items():
            new_changelog_group[categories_map[key] if categories_map.get(
                key) != None else key] = value
        changelog_group = new_changelog_group

    # Create Changelog
    if (output_file_enabled == "false" or output_file_enabled == None):
        print(generate_changelog(changelog_group, args[2]))
    elif (output_file_enabled == "true"):
        subprocess.getoutput(f'git checkout {output_file_branch}')

        generate_changelog_file(generate_changelog(changelog_group, args[2]))
    
        subprocess.getoutput(f'git add {output_file_path}')
        subprocess.getoutput(f'git commit -m "{output_file_commit_message}"')
    else:
        raise ValueError(
            "Unknown `output_file_enabled` in config file!!")


if __name__ == '__main__':
    main(sys.argv)
