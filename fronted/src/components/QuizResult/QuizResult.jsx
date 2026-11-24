import React, { useState } from "react";
import "./QuizResult.css";

export default function QuizResult({
  passageTitle,
  passage,
  onChangePassage, // Unseen: the generated text can be edited by the teacher
  questions,
  answerKey,
  onChangeQuestions, // אופציונלי לעריכה ידנית של השאלות
}) {
  const [showAnswers, setShowAnswers] = useState(false); // מוסתר כברירת מחדל

  return (
    <div className="quiz-result">
      {/* Passage box (Unseen only, editable textarea) */}
      {passage && (
        <div className="qr-panel">
          <div className="qr-panel-header">
            <span>📖 {passageTitle || "Text"}</span>
          </div>
          <textarea
            className="qr-textarea"
            style={{ fontFamily: "inherit", minHeight: 260 }}
            value={passage}
            onChange={(e) => onChangePassage?.(e.target.value)}
          />
        </div>
      )}

      {/* Questions box (editable textarea) */}
      <div className="qr-panel">
        <div className="qr-panel-header">
          <span>📝 Questions</span>
        </div>
        <textarea
          className="qr-textarea"
          value={questions || ""}
          onChange={(e) => onChangeQuestions?.(e.target.value)}
          placeholder="Questions will appear here..."
        />
      </div>

      {/* Answer Key box (read-only, collapsible) */}
      <div className="qr-panel">
        <div className="qr-panel-header qr-header-row">
          <span>✅ Answer Key</span>
          <button
            type="button"
            className="qr-toggle"
            onClick={() => setShowAnswers((s) => !s)}
          >
            {showAnswers ? "Hide" : "Show"}
          </button>
        </div>

        {showAnswers ? (
          <pre className="qr-pre" style={{ whiteSpace: "pre-wrap" }}>
            {answerKey || "—"}
          </pre>
        ) : (
          <div className="qr-collapsed-hint">Hidden</div>
        )}
      </div>
    </div>
  );
}