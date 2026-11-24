import React from 'react';
import './QuizForm.css';

const TYPE_OPTIONS = [
  { value: 'reading', label: '📖 Reading Comprehension' },
  { value: 'grammar', label: '✏️ Grammar' },
  { value: 'vocabulary', label: '🔤 Vocabulary' },
  { value: 'truefalse', label: '✅ True / False' },
];

const MAX_TOTAL = 15;

function QuizForm({
  mode,
  setMode,
  text,
  setText,
  description,
  setDescription,
  level,
  setLevel,
  counts,
  setCounts,
}) {
  const total = TYPE_OPTIONS.reduce((sum, t) => sum + (counts[t.value] || 0), 0);

  const updateCount = (type, value) =>
    setCounts((prev) => ({ ...prev, [type]: Number(value) }));

  return (
    <>
      <div className="form-label">
        <span className="form-label-text">🧭 How do you want to start?</span>
        <div className="form-mode">
          <button
            type="button"
            className={`form-mode-btn ${mode === 'paste' ? 'form-mode-btn--active' : ''}`}
            aria-pressed={mode === 'paste'}
            onClick={() => setMode('paste')}
          >
            📋 I have a text
          </button>
          <button
            type="button"
            className={`form-mode-btn ${mode === 'unseen' ? 'form-mode-btn--active' : ''}`}
            aria-pressed={mode === 'unseen'}
            onClick={() => setMode('unseen')}
          >
            ✨ Unseen – create a text from a description
          </button>
        </div>
      </div>

      {mode === 'paste' ? (
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
      ) : (
        <label className="form-label">
          <span className="form-label-text">✍️ Describe the text:</span>
          <textarea
            className="form-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="A short description, a topic or a plot. For example: a boy gets lost in a big city and a stranger helps him find his way home."
            rows="4"
            maxLength={1000}
            required
          />
          <div className="form-hint">
            The AI will write a text suited to the selected level, and then create the questions from it.
          </div>
        </label>
      )}

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
          <option value="C1">C1 - Advanced</option>
          <option value="C2">C2 - Proficiency</option>
        </select>
      </label>

      <div className="form-label">
        <span className="form-label-text">❓ Question types and amounts:</span>

        <div className="form-types">
          {TYPE_OPTIONS.map((t) => (
            <div className="form-type-row" key={t.value}>
              <label className="form-type-name" htmlFor={`count-${t.value}`}>
                {t.label}
              </label>
              <select
                id={`count-${t.value}`}
                className="form-select form-select--count"
                value={counts[t.value] || 0}
                onChange={(e) => updateCount(t.value, e.target.value)}
              >
                {Array.from({ length: MAX_TOTAL + 1 }, (_, i) => i).map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>

        <div className={`form-total ${total > MAX_TOTAL ? 'form-total--over' : ''}`}>
          Total: {total} / {MAX_TOTAL} questions
          {total === 0 && ' – choose at least one question'}
          {total > MAX_TOTAL && ' – too many, please reduce'}
        </div>

        <div className="form-hint">
          Questions always follow the order of the text, whatever their type.
        </div>
      </div>
    </>
  );
}

export default QuizForm;