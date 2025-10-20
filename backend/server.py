from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Literal, Optional
from main import create_quiz_flow, chat_edit_flow

# -------- Types --------
Level = Literal["A1", "A2", "B1", "B2"]
QuizType = Literal["reading", "grammar", "vocabulary"]


# -------- DTOs --------
class GenerateQuizRequest(BaseModel):
    source_text: str = Field(..., min_length=10)
    level: Level
    quizType: QuizType


class GenerateQuizResponse(BaseModel):
    result: str  # plain text


class ChatEditRequest(BaseModel):
    quiz_text: str = Field(..., min_length=1)  # The full text of the current quiz
    message: str = Field(..., min_length=1)  # The user's edit instruction or message


class ChatEditResponse(BaseModel):
    result: str


class ExportDocxRequest(BaseModel):
    content: str = Field(..., min_length=1)
    filename: Optional[str] = None  # optional suggested filename (without .docx)


# -------- App --------
app = FastAPI(title="Quiz API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- Routes --------
@app.get("/health")  # Defines a GET endpoint at /health to check server status
async def health():
    return {"status": "ok"}


@app.post("/api/quizzes/create", response_model=GenerateQuizResponse)
async def create_quiz(req: GenerateQuizRequest):
    """Creates a new quiz based on text, level, and type."""
    try:
        text = await create_quiz_flow(req.source_text, req.level, req.quizType)
        return GenerateQuizResponse(result=text)
    except Exception as e:
        print(f"[ERROR] create_quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quizzes/chat", response_model=ChatEditResponse)
async def chat_edit(req: ChatEditRequest):
    """Handles chat requests to modify or extend an existing quiz."""
    try:
        edited = await chat_edit_flow(req.quiz_text, req.message)
        return ChatEditResponse(result=edited)
    except Exception as e:
        print(f"[ERROR] chat_edit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quizzes/export/docx")
async def export_quiz_docx(req: ExportDocxRequest):
    """
    Converts plain-text quiz to a DOCX and returns the file for download.
    Requires file_generator.generate_docx_from_text().
    """
    try:
        from file_generator import generate_docx_from_text
        out_path = generate_docx_from_text(req.content, req.filename or "quiz")
        download_name = (req.filename or "quiz") + ".docx"
        return FileResponse(
            out_path,
            filename=download_name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        print(f"[ERROR] export_docx: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------- Entry Point --------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
