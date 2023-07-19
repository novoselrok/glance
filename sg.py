import os
import re
import requests
from typing import Dict, Any

SOURCEGRAPH_API_URL = "https://sourcegraph.com/.api/graphql"
SOURCEGRAPH_API_TOKEN = os.environ["SOURCEGRAPH_API_TOKEN"]
SOURCEGRAPH_API_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"token {SOURCEGRAPH_API_TOKEN}",
}


SOURCEGRAPH_GRAPHQL_HIGHLIGHTED_FILE_RANGE_QUERY = """
    query HighlightedFile(
        $repoName: String!
        $commitID: String!
        $filePath: String!
        $startLine: Int!
        $endLine: Int!
    ) {
        repository(name: $repoName) {
            commit(rev: $commitID) {
                file(path: $filePath) {
                    content
                    highlight(disableTimeout: true, format: HTML_HIGHLIGHT) {
                        lineRanges(ranges: [{startLine: $startLine, endLine: $endLine}])
                    }
                }
            }
        }
    }
"""


def query_highlighted_file_line_range(
    repo_name: str, commit_id: str, file_path: str, start_line: int, end_line: int
):
    data = {
        "query": SOURCEGRAPH_GRAPHQL_HIGHLIGHTED_FILE_RANGE_QUERY,
        "variables": {
            "repoName": repo_name,
            "commitID": commit_id,
            "filePath": file_path,
            "startLine": start_line,
            "endLine": end_line,
        },
    }
    response = requests.post(
        SOURCEGRAPH_API_URL, headers=SOURCEGRAPH_API_HEADERS, json=data
    )
    file = response.json()["data"]["repository"]["commit"]["file"]
    content = file["content"]
    highlighted_range = "\n".join(file["highlight"]["lineRanges"][0])
    return content, highlighted_range


url_regexp = re.compile(r"https:\/\/sourcegraph\.com\/(.*?)(@.*)?\/-\/blob\/(.*)")


def parse_url(url: str) -> Dict[str, Any]:
    groups = url_regexp.match(url)
    repo_name, commit_id, file_path = groups.group(1), groups.group(2), groups.group(3)
    if commit_id:
        commit_id = commit_id[1:]
    else:
        commit_id = "HEAD"

    if "?" in file_path:
        file_path = file_path.split("?")[0]

    return repo_name, commit_id, file_path
