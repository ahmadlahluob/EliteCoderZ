import requests

LEETCODE_URL = "https://leetcode.com/graphql"

RECENT_SOLVES_QUERY = """
query recentAcSubmissions($username: String!) {
  recentAcSubmissionList(username: $username, limit: 20) {
    title
    timestamp
  }
}
"""

RANDOM_PROBLEM_QUERY = """
query randomQuestion {
  randomQuestion {
    title
    titleSlug
  }
}
"""


def get_recent_accepted_problems(username):
    payload = {
        "query": RECENT_SOLVES_QUERY,
        "variables": {
            "username": username
        }
    }
    resp = requests.post(LEETCODE_URL, json=payload)
    if resp.status_code != 200:
        return []
    submissions = resp.json().get("data", {}).get("recentAcSubmissionList", [])
    return [sub["title"] for sub in submissions]


def fetch_random_problem():
    payload = {"query": RANDOM_PROBLEM_QUERY}
    resp = requests.post(LEETCODE_URL, json=payload)
    if resp.status_code != 200:
        return {
            "title": "Fallback Problem",
            "url": "https://leetcode.com/problemset/all/"
        }
    data = resp.json().get("data", {}).get("randomQuestion", {})
    return {
        "title": data.get("title", "Fallback Problem"),
        "url": f"https://leetcode.com/problems/{data.get('titleSlug', '')}/"
    }
