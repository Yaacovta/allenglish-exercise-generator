import React, { useState } from "react";
import "./DownloadDocxButton.css";

export default function DownloadDocxButton({ content }) {
  const [isDownloadingTeacher, setIsDownloadingTeacher] = useState(false);
  const [isDownloadingStudent, setIsDownloadingStudent] = useState(false);

  const extractErrorMessage = async (res) => {
    const json = await res.json().catch(() => null);
    if (json && json.detail !== undefined) {
      if (typeof json.detail === "string") return json.detail;
      return JSON.stringify(json.detail, null, 2);
    }
    return `HTTP ${res.status}`;
  };

  const downloadDocx = async (includeAnswers) => {
    if (!content || !content.trim()) {
      alert("Nothing to download yet. Generate a quiz first.");
      return;
    }

    includeAnswers ? setIsDownloadingTeacher(true) : setIsDownloadingStudent(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/quizzes/export/docx", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          filename: includeAnswers ? "quiz_teacher" : "quiz_student",
          include_answers: includeAnswers,
        }),
      });

      if (!res.ok) throw new Error(await extractErrorMessage(res));

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = includeAnswers ? "quiz_with_answers.docx" : "quiz_without_answers.docx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Download failed: ${err.message}`);
    } finally {
      setIsDownloadingTeacher(false);
      setIsDownloadingStudent(false);
    }
  };

  const disabled = !content || !content.trim() || isDownloadingTeacher || isDownloadingStudent;

  return (
    <div className="download-docx-actions download-docx-actions--inline">
      <button
        type="button"
        className={`download-docx-btn download-docx-btn--wide download-docx-btn--teacher ${
          isDownloadingTeacher ? "download-docx-btn--loading" : ""
        }`}
        disabled={disabled}
        onClick={() => downloadDocx(true)}
      >
        {isDownloadingTeacher ? "Preparing…" : "👨‍🏫 With Answers"}
      </button>

      <button
        type="button"
        className={`download-docx-btn download-docx-btn--wide download-docx-btn--student ${
          isDownloadingStudent ? "download-docx-btn--loading" : ""
        }`}
        disabled={disabled}
        onClick={() => downloadDocx(false)}
      >
        {isDownloadingStudent ? "Preparing…" : "🎓 Without Answers"}
      </button>
    </div>
  );
}
