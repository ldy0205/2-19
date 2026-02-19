#!/usr/bin/env python3
"""
AI 프롬프트 가이드 사이트 — GitHub Commit & Push → Netlify 배포 스크립트
사용 전 아래 CONFIG 섹션의 값을 채워주세요.
"""

import subprocess
import sys
import os
import json
import urllib.request
import urllib.error
from pathlib import Path

# ─────────────────────────────────────────
#  CONFIG  ← 여기만 수정하세요
# ─────────────────────────────────────────
GITHUB_TOKEN    = "YOUR_GITHUB_TOKEN"          # GitHub Personal Access Token (repo 권한 필요)
GITHUB_USERNAME = "YOUR_GITHUB_USERNAME"       # GitHub 유저명
REPO_NAME       = "prompt-guide"               # 생성할(또는 기존) 저장소 이름

NETLIFY_TOKEN   = "YOUR_NETLIFY_TOKEN"         # Netlify Personal Access Token
# 기존 Netlify 사이트에 배포하려면 Site ID 입력, 새로 만들려면 빈 문자열 ""
NETLIFY_SITE_ID = ""

COMMIT_MESSAGE  = "feat: AI 프롬프트 완전 가이드 사이트 배포"
BRANCH          = "main"
# ─────────────────────────────────────────

BASE_DIR = Path(__file__).parent


def run(cmd: list[str], cwd=None, check=True) -> subprocess.CompletedProcess:
    """셸 명령 실행 + 출력"""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or BASE_DIR, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0 and check:
        print(f"[ERROR] {result.stderr.strip()}")
        sys.exit(1)
    return result


def api_request(url: str, method: str = "GET", data: dict = None, token: str = None) -> dict:
    """간단한 HTTP 요청 헬퍼"""
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"token {token}")
    body = json.dumps(data).encode() if data else None
    try:
        with urllib.request.urlopen(req, data=body, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"[HTTP ERROR {e.code}] {err}")
        sys.exit(1)


# ─── STEP 1: 유효성 검사 ──────────────────
def validate_config():
    print("\n[1/5] 설정 확인 중...")
    placeholders = [
        ("GITHUB_TOKEN", GITHUB_TOKEN),
        ("GITHUB_USERNAME", GITHUB_USERNAME),
        ("NETLIFY_TOKEN", NETLIFY_TOKEN),
    ]
    for name, val in placeholders:
        if val.startswith("YOUR_"):
            print(f"  ✗ {name} 값을 CONFIG 섹션에 입력해주세요.")
            sys.exit(1)
    if not (BASE_DIR / "index.html").exists():
        print("  ✗ index.html 파일이 없습니다. deploy.py와 같은 폴더에 두세요.")
        sys.exit(1)
    print("  ✓ 설정 확인 완료")


# ─── STEP 2: GitHub 저장소 준비 ───────────
def setup_github_repo():
    print(f"\n[2/5] GitHub 저장소 준비: {GITHUB_USERNAME}/{REPO_NAME}")
    repo_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}"
    check = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
         "-H", f"Authorization: token {GITHUB_TOKEN}", repo_url],
        capture_output=True, text=True
    )
    status = check.stdout.strip()

    if status == "404":
        print(f"  저장소 없음 → 새로 생성...")
        api_request(
            "https://api.github.com/user/repos",
            method="POST",
            data={"name": REPO_NAME, "private": False, "description": "AI 프롬프트 완전 가이드"},
            token=GITHUB_TOKEN,
        )
        print(f"  ✓ 저장소 생성 완료")
    else:
        print(f"  ✓ 기존 저장소 사용")

    remote = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
    return remote


# ─── STEP 3: Git 초기화 및 커밋 ───────────
def git_commit_push(remote: str):
    print("\n[3/5] Git commit & push...")

    git_dir = BASE_DIR / ".git"
    if not git_dir.exists():
        run(["git", "init"])
        run(["git", "checkout", "-b", BRANCH], check=False)

    # .gitignore 생성
    gitignore = BASE_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("__pycache__/\n*.pyc\n.DS_Store\n.env\n")

    run(["git", "add", "."])

    # 커밋할 변경 사항이 없으면 스킵
    diff = subprocess.run(
        ["git", "diff", "--cached", "--stat"], capture_output=True, text=True, cwd=BASE_DIR
    )
    if not diff.stdout.strip():
        print("  → 변경 사항 없음, 커밋 스킵")
    else:
        run(["git", "commit", "-m", COMMIT_MESSAGE])
        print("  ✓ 커밋 완료")

    # 리모트 설정
    remotes = subprocess.run(
        ["git", "remote"], capture_output=True, text=True, cwd=BASE_DIR
    ).stdout.strip()
    if "origin" not in remotes.split():
        run(["git", "remote", "add", "origin", remote])
    else:
        run(["git", "remote", "set-url", "origin", remote])

    # 현재 브랜치 확인 후 push
    branch_now = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, cwd=BASE_DIR
    ).stdout.strip()

    run(["git", "push", "-u", "origin", f"{branch_now}:{BRANCH}", "--force"])
    print(f"  ✓ https://github.com/{GITHUB_USERNAME}/{REPO_NAME} 에 push 완료")


# ─── STEP 4: Netlify 배포 ─────────────────
def deploy_netlify():
    print("\n[4/5] Netlify 배포 중...")

    site_id = NETLIFY_SITE_ID

    if not site_id:
        # 새 사이트 생성
        site = api_request(
            "https://api.netlify.com/api/v1/sites",
            method="POST",
            data={"name": f"{GITHUB_USERNAME}-{REPO_NAME}"},
            token=NETLIFY_TOKEN,
        )
        site_id = site.get("id", "")
        site_url = site.get("ssl_url") or site.get("url", "")
        print(f"  ✓ Netlify 사이트 생성: {site_url}")
    else:
        site_info = api_request(
            f"https://api.netlify.com/api/v1/sites/{site_id}",
            token=NETLIFY_TOKEN,
        )
        site_url = site_info.get("ssl_url") or site_info.get("url", "")
        print(f"  ✓ 기존 사이트 사용: {site_url}")

    # GitHub 연동 배포 (사이트에 repo 연결)
    repo_path = f"{GITHUB_USERNAME}/{REPO_NAME}"
    api_request(
        f"https://api.netlify.com/api/v1/sites/{site_id}",
        method="PATCH",
        data={
            "repo": {
                "provider": "github",
                "repo": repo_path,
                "branch": BRANCH,
                "cmd": "",                   # 빌드 명령 없음 (정적 HTML)
                "dir": ".",
            }
        },
        token=NETLIFY_TOKEN,
    )
    print(f"  ✓ GitHub 저장소 연결 완료")

    # 수동 deploy trigger
    deploy = api_request(
        f"https://api.netlify.com/api/v1/sites/{site_id}/deploys",
        method="POST",
        data={"branch": BRANCH},
        token=NETLIFY_TOKEN,
    )
    deploy_url = deploy.get("deploy_ssl_url") or deploy.get("deploy_url") or site_url
    print(f"  ✓ 배포 시작 (ID: {deploy.get('id', 'N/A')})")
    return site_url, deploy_url


# ─── STEP 5: 결과 출력 ────────────────────
def print_summary(github_url: str, netlify_url: str):
    print("\n[5/5] 배포 완료 요약")
    print("=" * 50)
    print(f"  GitHub  : https://github.com/{GITHUB_USERNAME}/{REPO_NAME}")
    print(f"  Netlify : {netlify_url}")
    print("=" * 50)
    print("\n  ⚡ Netlify가 빌드를 마치면 (보통 1~2분) 사이트가 활성화됩니다.")
    print("  📌 Netlify 대시보드: https://app.netlify.com\n")


# ─── MAIN ────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  AI 프롬프트 가이드 — 자동 배포 스크립트")
    print("=" * 50)

    validate_config()
    remote = setup_github_repo()
    git_commit_push(remote)
    netlify_url, deploy_url = deploy_netlify()
    print_summary(f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}", netlify_url)
