import os
import json
import requests
from github import Github
import ollama
import re

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPOSITORY')
PR_NUMBER = os.getenv('GITHUB_REF').split("/")[-1]  # 안전한 PR 번호 추출
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

# 파일별 리뷰 분석을 위한 프롬프트 생성
prompt = f"""
You are a senior software engineer conducting a code review based on the provided git diff. For each modified file, provide a detailed review that includes:

1. **Functionality Changes**: Describe what the changes in the file do.
2. **Code Style & Best Practices**: Highlight good coding practices used and suggest improvements if needed.
3. **Performance Considerations**: Discuss any potential performance issues or optimizations.
4. **Technical Explanations**: Explain relevant concepts or technologies used in the code.
5. **Potential Issues & Fixes**: Identify any possible bugs or areas of concern and suggest fixes.
6. **Additional Learning Resources**: Suggest any useful resources for further learning.

Ensure that the review is formatted per file, using a structured and easy-to-read format, response in Korean.

<git diff>
{diff_content}
</git diff>
"""

client = ollama.Client(host=OLLAMA_API_URL)
response = client.generate(model="deepseek-coder-v2", prompt=prompt, options={"num_ctx": 4096})

review_comments = response.get("response", "No response from Ollama.")

# JSON 데이터 추출
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
