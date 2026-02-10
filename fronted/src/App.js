import React, { useState } from 'react';
import './App.css';

import QuizForm from './components/QuizForm/QuizForm';
import GenerateButton from './components/GenerateButton/GenerateButton';
import QuizResult from './components/QuizResult/QuizResult';
import QuizChat from './components/QuizChat/QuizChat';
import DownloadDocxButton from './components/DownloadDocxButton/DownloadDocxButton';
import { splitQuiz, joinQuiz } from './utils/quizParsing';

function App() {
  const [text, setText] = useState('');
  const [level, setLevel] = useState('');
  const [quizType, setQuizType] = useState('');

  // NEW: user must choose number of questions (no default)
  const [questionCount, setQuestionCount] = useState('');

  const [questions, setQuestions] = useState('');
  const [answerKey, setAnswerKey] = useState('');

  // loading indicator while AI generates
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isGenerating) return;

    setIsGenerating(true);
    try {
      const payload = {
        source_text: text,
        level: (level || '').split(' ')[0],        // A1/A2/B1/B2
        quizType: (quizType || '').toLowerCase(),  // reading/grammar/vocabulary/truefalse
        question_count: parseInt(questionCount, 10), // 1..15
      };

      const res = await fetch('http://127.0.0.1:8000/api/quizzes/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json(); // { result: "..." }
      const parts = splitQuiz(data.result);
      setQuestions(parts.questions);
      setAnswerKey(parts.answerKey);
    } catch (err) {
      console.error('Generate failed:', err);
      setQuestions(`ERROR: ${err.message}`);
      setAnswerKey('');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleChatMessage = async (message) => {
    const combined = joinQuiz(questions, answerKey);

    const res = await fetch('http://127.0.0.1:8000/api/quizzes/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quiz_text: combined, message }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json(); // { result: "..." }
    const parts = splitQuiz(data.result);
    setQuestions(parts.questions);
    setAnswerKey(parts.answerKey);
  };

  const combinedForDownload = joinQuiz(questions, answerKey);

  return (
    <div className="app-container">
      <h2 className="form-title">🎓 Create a New Quiz</h2>

      <form onSubmit={handleSubmit}>
        <QuizForm
          text={text} setText={setText}
          level={level} setLevel={setLevel}
          quizType={quizType} setQuizType={setQuizType}
          questionCount={questionCount} setQuestionCount={setQuestionCount}
        />

        <GenerateButton isLoading={isGenerating} />

        {isGenerating && (
          <div className="ai-loading" role="status" aria-live="polite">
            <span className="ai-loading__spinner" aria-hidden="true"></span>
            <div className="ai-loading__text">
              <div className="ai-loading__title">AI is preparing your quiz…</div>
              <div className="ai-loading__subtitle">Please wait a few seconds.</div>
            </div>
          </div>
        )}
      </form>

      {(questions || answerKey) && (
        <>
          <QuizResult
            questions={questions}
            answerKey={answerKey}
            onChangeQuestions={setQuestions}
            onChangeAnswerKey={setAnswerKey}
          />
          <QuizChat onSendMessage={handleChatMessage} />
          <DownloadDocxButton content={combinedForDownload} />
        </>
      )}
    </div>
  );
}

export default App;
