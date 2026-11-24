from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator
from typing import List, Literal, Optional

from main import create_quiz_flow, create_unseen_flow, chat_edit_flow

# -------- Types --------
Level = Literal["A1", "A2", "B1", "B2", "C1", "C2"]
QuizType = Literal["reading", "grammar", "vocabulary", "truefalse"]

MAX_TOTAL_QUESTIONS = 15


def _check_sections(sections) -> None:
    types = [s.quizType for s in sections]
    if len(set(types)) != len(types):
        raise ValueError("Each quiz type can appear only once.")
    if sum(s.count for s in sections) > MAX_TOTAL_QUESTIONS:
        raise ValueError(f"A quiz can have at most {MAX_TOTAL_QUESTIONS} questions in total.")


# -------- DTOs --------
class SectionSpec(BaseModel):
    quizType: QuizType
    count: int = Field(..., ge=1, le=MAX_TOTAL_QUESTIONS)


class GenerateQuizRequest(BaseModel):
    source_text: str = Field(..., min_length=10)
    level: Level
    sections: List[SectionSpec] = Field(..., min_length=1, max_length=4)

    @model_validator(mode="after")
    def check_sections(self):
        _check_sections(self.sections)
        return self


class GenerateQuizResponse(BaseModel):
    result: str


class UnseenRequest(BaseModel):
    description: str = Field(..., min_length=3, max_length=1000)
    level: Level
    sections: List[SectionSpec] = Field(..., min_length=1, max_length=4)

    @model_validator(mode="after")
    def check_sections(self):
        _check_sections(self.sections)
        return self


class UnseenResponse(BaseModel):
    title: str
    passage: str
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
    passage_title: Optional[str] = None  # Unseen: title of the generated text
    passage: Optional[str] = None        # Unseen: the generated text


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
            [(s.quizType, s.count) for s in req.sections],
        )
        return GenerateQuizResponse(result=quiz_text)
    except Exception as e:
        print("[ERROR create_quiz]", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/unseen/create", response_model=UnseenResponse)
async def create_unseen(req: UnseenRequest):
    try:
        title, passage, quiz_text = await create_unseen_flow(
            req.description,
            req.level,
            [(s.quizType, s.count) for s in req.sections],
        )
        return UnseenResponse(title=title, passage=passage, result=quiz_text)
    except Exception as e:
        print("[ERROR create_unseen]", e)
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
            passage_title=req.passage_title,
            passage=req.passage,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)