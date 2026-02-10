import React from 'react';
import './GenerateButton.css';

function GenerateButton({ isLoading }) {
  return (
    <button
      type="submit"
      className={`generate-btn ${isLoading ? 'generate-btn--loading' : ''}`}
      disabled={isLoading}
    >
      {isLoading ? (
        <>
          <span className="generate-btn__spinner" aria-hidden="true"></span>
          <span className="generate-btn__text">AI is generating your quiz…</span>
        </>
      ) : (
        <span className="generate-btn__text">⚡ Generate Quiz</span>
      )}
    </button>
  );
}

export default GenerateButton;
