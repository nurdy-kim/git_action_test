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

# ✅ diff.txt 파일 읽기
with open(diff_file, "r") as file:
    diff_content = file.read()

# ✅ 파일별로 git diff 분리하기
def split_diff_by_file(diff_text):
    file_diffs = {}
    current_file = None
    current_diff = []

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            # 기존 파일 저장
            if current_file and current_diff:
                file_diffs[current_file] = "\n".join(current_diff)

            # 새 파일 시작
            parts = line.split(" ")
            if len(parts) > 2:
                file_path = parts[2][2:]  # "a/" 또는 "b/" 접두어 제거
                current_file = file_path
                current_diff = [line]  # 새로운 diff 시작
        elif current_file:
            current_diff.append(line)

    # 마지막 파일 저장
    if current_file and current_diff:
        file_diffs[current_file] = "\n".join(current_diff)

    return file_diffs

file_diffs = split_diff_by_file(diff_content)

# ✅ Ollama 클라이언트 설정
client = ollama.Client(host=OLLAMA_API_URL)

# ✅ 각 파일별로 Ollama에 요청
all_review_comments = []
for file_path, file_diff in file_diffs.items():
    print(f"🔍 Reviewing {file_path}...")

    prompt = f"""
You are a senior software engineer conducting a code review based on the provided git diff.
Analyze the changes in the file: **{file_path}**, and provide feedback.
Make sure your review covers:
1. **Functionality Changes**: What does this change do?
2. **Code Style & Best Practices**: Any improvements or issues?
3. **Performance Considerations**: Potential optimizations?
4. **Technical Explanations**: Any complex concepts involved?
5. **Potential Issues & Fixes**: Any possible bugs or vulnerabilities?
6. **Additional Learning Resources**: Helpful references.

Format:
[
  {{"path": "{file_path}", "line": <line_number>, "text": "<review_comment>", "side": "RIGHT"}}
]

<git diff>
{file_diff}
</git diff>
"""

    response = client.generate(model="deepseek-coder-v2", prompt=prompt, options={"num_ctx": 4096})

    review_comments = response.get("response", "No response from Ollama.")
    print("res: "review_comments)
    # ✅ JSON 부분만 추출
    match = re.search(r"```json\n(.*?)\n```", review_comments, re.DOTALL)
    if match:
        review_comments = match.group(1).strip()

    # ✅ JSON 파싱 시도
    try:
        parsed_comments = json.loads(review_comments)
        all_review_comments.extend(parsed_comments)  # 모든 결과를 합치기
        print(f"✅ {file_path} 리뷰 완료")
    except json.JSONDecodeError as e:
        print(f"🚨 JSON 파싱 오류 발생 for {file_path}: {e}")
        print("👉 원본 데이터:", review_comments)

# 📁 JSON 파일로 저장
with open("res.txt", "w") as res_file:
    res_file.write(json.dumps(parsed_comments, indent=4))  # ✅ JSON 형식으로 저장

print(f"res : {parsed_comments}")

