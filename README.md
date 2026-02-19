# AI 프롬프트 완전 가이드

무역·비즈니스 실무에 초점을 맞춘 AI 프롬프트 엔지니어링 가이드 사이트입니다.

## 📁 파일 구조

```
/
├── index.html    ← 메인 사이트 (단일 HTML 파일)
├── deploy.py     ← GitHub + Netlify 자동 배포 스크립트
└── README.md
```

## 🚀 로컬 미리보기

```bash
# Python 내장 서버로 바로 실행
python3 -m http.server 8080
# 브라우저에서 http://localhost:8080 접속
```

## ⚙️ 배포 방법

### 방법 A: deploy.py 자동 배포 (권장)

1. `deploy.py` 파일 상단 **CONFIG 섹션** 수정:
   ```python
   GITHUB_TOKEN    = "ghp_xxxxx"          # GitHub PAT (repo 권한)
   GITHUB_USERNAME = "your-username"
   REPO_NAME       = "prompt-guide"
   NETLIFY_TOKEN   = "nfp_xxxxx"          # Netlify PAT
   NETLIFY_SITE_ID = ""                   # 신규 사이트: 빈 문자열
   ```

2. 실행:
   ```bash
   python3 deploy.py
   ```

### 방법 B: 수동 GitHub + Netlify 배포

```bash
# 1. Git 초기화 및 push
git init
git add .
git commit -m "첫 배포"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/prompt-guide.git
git push -u origin main
```

2. **Netlify** → New site → Import from GitHub → 저장소 선택  
   - Branch: `main`
   - Build command: (비워두기)
   - Publish directory: `.`  
   - **Deploy site** 클릭

## 🔑 토큰 발급

| 토큰 | 발급 경로 |
|------|-----------|
| GitHub PAT | Settings → Developer settings → Personal access tokens → `repo` 체크 |
| Netlify PAT | User settings → Applications → Personal access tokens |

## 📖 포함된 내용

1. 프롬프트 3가지 유형 (서술형 · 지침형 · 함수형)
2. 샷 프롬프팅 (Zero/One/Few-Shot)
3. 페르소나 패턴
4. 마크다운 구조화 프롬프트
5. 표현 강도 & 우선순위 시스템
6. 톤(말투) 지정
7. 대안 접근법 패턴 (4가지 유형)
8. 이용자 페르소나 패턴
9. 레시피 패턴
10. 뒤집힌 상호작용 패턴
11. 인지 검증자 패턴
