import os
import json
from github import Github
import ollama

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPOSITORY')
PR_NUMBER = os.getenv('GITHUB_EVENT_PULL_REQUEST_NUMBER')
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL')

github_client = Github(GITHUB_TOKEN)
repo = github_client.get_repo(REPO_NAME)
pr = repo.get_pull(int(PR_NUMBER))

diff_file = "diff.txt"
if not os.path.exists(diff_file):
    print("diff.txt not found.")
    exit(1)

with open(diff_file, "r") as file:
    diff_content = file.read()

prompt = f"""
You are a senior software engineer and need to perform a code review based on the results of a given git diff. Review the changed code from different perspectives and let us know if there are any changes that need to be made. If you see any code that needs to be fixed in the result of the git diff, you need to calculate the exact line number by referring to the “@@ -0,0 +0,0 @@” part. The output format is [{"path":"{ filepath }", "line": { line }, "text": { review comment }, "side": "RIGHT"}] format must be respected.
<git diff>{diff_content}</git diff>
"""

resposne = request.post(
    OLLAMA_API_URL,
    json={"model": "deepseek-coder-v2", "prompt" prompt, "stream": False}
)

if response.status_code == 200:
    review_comments = resposne.json().get("response", "No response from Ollama.")
else:
    review_comments = f"ERROR from Ollama: {response.text}"

# 리뷰 결과 저장
with open("res.txt", "w") as res_file:
    res_file.write(review_comments)

print("Save Results!")


