import React from 'react';
import './QuizForm.css';

function QuizForm({ text, setText, level, setLevel, quizType, setQuizType }) {
  return (
    <>
      <label className="form-label">
        <span className="form-label-text">📄 Source Text:</span>
        <textarea
          className="form-textarea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste the text here..."
          rows="8"
          required
        />
      </label>

      <label className="form-label">
        <span className="form-label-text">🎯 Select Level:</span>
        <select
          className="form-select"
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          required
        >
          <option value="">Choose level</option>
          <option value="A1">A1 - Beginner</option>
          <option value="A2">A2 - Elementary</option>
          <option value="B1">B1 - Intermediate</option>
          <option value="B2">B2 - Upper Intermediate</option>
        </select>
      </label>

      <label className="form-label">
        <span className="form-label-text">❓ Quiz Type:</span>
        <select
          className="form-select"
          value={quizType}
          onChange={(e) => setQuizType(e.target.value)}
          required
        >
          <option value="">Choose quiz type</option>
          <option value="reading">Reading Comprehension</option>
          <option value="grammar">Grammar</option>
          <option value="vocabulary">Vocabulary</option>
        </select>
      </label>
    </>
  );
}

export default QuizForm;
