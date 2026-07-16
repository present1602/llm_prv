"""검증용 목(mock) OpenAI 호환 LLM 서버.

Ollama 없이 전체 파이프라인(생성→재생성→내보내기)을 end-to-end로 확인하기 위한
최소 서버. 실제 배포에는 사용하지 않는다.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/v1/models")
def models():
    return {"data": [{"id": "exaone3.5:7.8b"}]}


@app.post("/v1/chat/completions")
async def chat(body: dict):
    user = body["messages"][-1]["content"]
    # 어떤 섹션을 요청했는지 프롬프트에서 추출
    marker = "작성할 섹션: 「"
    title = "섹션"
    if marker in user:
        title = user.split(marker, 1)[1].split("」", 1)[0]
    content = f"[MOCK] 「{title}」 섹션 본문입니다. 발명자 입력을 바탕으로 생성되었습니다."
    return JSONResponse(
        {"choices": [{"message": {"role": "assistant", "content": content}}]}
    )
