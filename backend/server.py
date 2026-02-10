from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Literal, Optional

from main import create_quiz_flow, chat_edit_flow

# -------- Types --------
Level = Literal["A1", "A2", "B1", "B2"]
QuizType = Literal["reading", "grammar", "vocabulary", "truefalse"]


# -------- DTOs --------
class GenerateQuizRequest(BaseModel):
    source_text: str = Field(..., min_length=10)
    level: Level
    quizType: QuizType
    question_count: int = Field(..., ge=1, le=15)


class GenerateQuizResponse(BaseModel):
    result: str


class ChatEditRequest(BaseModel):
    quiz_text: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ChatEditResponse(BaseModel):
    result: str


class ExportDocxRequest(BaseModel):
    content: str = Field(..., min_length=1)
    filename: Optional[str] = "quiz"
    include_answers: bool = True  # NEW


# -------- App --------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- Routes --------
@app.post("/api/quizzes/create", response_model=GenerateQuizResponse)
async def create_quiz(req: GenerateQuizRequest):
    try:
        quiz_text = await create_quiz_flow(
            req.source_text,
            req.level,
            req.quizType,
            req.question_count,
        )
        return GenerateQuizResponse(result=quiz_text)
    except Exception as e:
        print("[ERROR create_quiz]", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quizzes/chat", response_model=ChatEditResponse)
async def chat_edit(req: ChatEditRequest):
    try:
        edited = await chat_edit_flow(req.quiz_text, req.message)
        return ChatEditResponse(result=edited)
    except Exception as e:
        print("[ERROR chat_edit]", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quizzes/export/docx")
async def export_docx(req: ExportDocxRequest):
    try:
        from file_generator import generate_docx_from_text

        filename = (req.filename or "quiz").strip() or "quiz"
        out_path = generate_docx_from_text(
            req.content,
            filename_hint=filename,
            include_answers=req.include_answers,  
        )

        suffix = "teacher" if req.include_answers else "student"
        download_name = f"{filename}_{suffix}.docx"

        return FileResponse(
            out_path,
            filename=download_name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        print("[ERROR export_docx]", e)
        raise HTTPException(status_code=500, detail=str(e))
