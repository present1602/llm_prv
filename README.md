# 특허 명세서 초안 자동 작성 — 폐쇄형 LLM MVP

발명 아이디어를 입력하면 KIPO 서식의 특허 명세서 **초안**을 자동 생성하는
폐쇄형(로컬 전용) 시스템. 외부 API를 호출하지 않고 로컬 LLM(Ollama)만 사용한다.

플랜: [DRAFT_PLAN.md](DRAFT_PLAN.md)

## 구성

- `backend/` — FastAPI. 명세서 스키마·프롬프트 오케스트레이터, PDF 파서, Ollama 클라이언트, Markdown/DOCX 내보내기
- `frontend/` — React(Vite). 발명 정보 입력 폼 + 섹션별 결과 편집·재생성 UI
- `file_samples/` — KIPO 실제 문서 샘플 (파싱 검증용)

## 실행

### 1. LLM (Ollama) — 실제 생성에 필요

```bash
# 설치: https://ollama.com  (brew install ollama)
ollama serve                 # 로컬 LLM 서버 (11434 포트)
ollama pull exaone3.5:7.8b   # 또는  qwen2.5:14b
```

모델을 바꾸려면 환경변수로 지정:

```bash
export LLM_MODEL=qwen2.5:14b        # 기본값: exaone3.5:7.8b
export LLM_BASE_URL=http://localhost:11434/v1   # vLLM 등으로 교체 가능
```

### 2. 백엔드

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8000 --reload
```

`GET http://localhost:8000/api/health` 로 LLM 연결 상태 확인 (`model_ready: true`).

### 3. 프런트엔드

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (/api 는 8000 백엔드로 프록시)
```

## 사용 흐름

1. 발명 정보(설명·문제·핵심 특징 등) 입력, 필요 시 참고 PDF 업로드(텍스트 자동 추출)
2. **명세서 초안 생성** → 9개 섹션(명칭·기술분야·배경기술·해결과제·해결수단·효과·실시예·청구범위·요약서) 순차 생성
3. 섹션별로 직접 편집하거나 **재생성**(추가 지시 반영)
4. **Markdown / DOCX** 로 내보내기

## API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/health` | 서비스·LLM 상태 |
| GET | `/api/sections` | 명세서 섹션 스키마 |
| POST | `/api/parse` | PDF → 텍스트 추출 |
| POST | `/api/generate` | 전체(또는 지정) 섹션 생성 |
| POST | `/api/regenerate` | 단일 섹션 재생성 |
| POST | `/api/export/markdown` · `/api/export/docx` | 문서 내보내기 |

## 참고

- `backend/mock_llm.py` 는 Ollama 없이 파이프라인을 점검하기 위한 검증용 목 서버다.
  `uvicorn mock_llm:app --port 11434` 로 띄우면 LLM 없이 전체 흐름을 확인할 수 있다.
- 생성물은 **초안**이며 변리사·발명자의 검토·수정을 전제로 한다.
- 다음 단계(Phase 2~): 선행문헌 RAG, 파인튜닝, HWP 출력 — [DRAFT_PLAN.md](DRAFT_PLAN.md) 참고.
