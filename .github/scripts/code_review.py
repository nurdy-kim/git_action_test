import os
import json
import requests
from github import Github
import ollama
import re

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPOSITORY')
PR_NUMBER = os.getenv('GITHUB_REF').split("/")[2]
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
You are a senior software engineer conducting a code review based on the provided git diff. Please analyze the changes from multiple perspectives, including correctness, security, readability, and best practices. Identify any potential improvements or necessary fixes.

For each identified issue, provide the exact file path and line number by referring to the context markers (e.g., @@ -0,0 +0,0 @@) in the diff. Ensure the output is formatted as a structured JSON list:

[
  {{"path": "<file_path>", "line": <line_number>, "text": "<review_comment>", "side": "RIGHT"}}
]

<git diff>
{diff_content}
</git diff>
"""

client = ollama.Client(host=OLLAMA_API_URL)

response = client.generate(model="deepseek-coder-v2", prompt=prompt, options={"num_ctx": 4096})

# response = requests.post(
#     OLLAMA_API_URL,
#     json={"model": "deepseek-coder-v2", "prompt": prompt, "stream": False}
# )

review_comments = response.get("response", "No response from Ollama.")

match = re.search(r"```json\n(.*?)\n```", review_comments, re.DOTALL)
if match:
    review_comments = match.group(1).strip()  # ✅ JSON 부분만 추출

# 🚀 2️⃣ JSON 파싱 시도
try:
    parsed_comments = json.loads(review_comments)
    print("✅ 정상적인 JSON 파싱 완료")
except json.JSONDecodeError as e:
    print("🚨 JSON 파싱 오류 발생:", e)
    print("👉 원본 데이터:", review_comments)
    exit(1)  # JSON 오류 발생 시 종료

# 📁 JSON 파일로 저장
with open("res.txt", "w") as res_file:
    res_file.write(json.dumps(parsed_comments, indent=4))  # ✅ JSON 형식으로 저장

print(f"res : {parsed_comments}")


