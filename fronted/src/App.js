import React, { useState } from 'react';
import './App.css';

import QuizForm from './components/QuizForm/QuizForm';
import GenerateButton from './components/GenerateButton/GenerateButton';
import QuizResult from './components/QuizResult/QuizResult';
import QuizChat from './components/QuizChat/QuizChat';
import DownloadDocxButton from './components/DownloadDocxButton/DownloadDocxButton';
import { splitQuiz, joinQuiz } from './utils/quizParsing';

const QUIZ_TYPES = ['reading', 'grammar', 'vocabulary', 'truefalse'];
const MAX_TOTAL = 15;

function App() {
  // 'paste' = the teacher pastes a text, 'unseen' = the AI writes the text from a description
  const [mode, setMode] = useState('paste');

  const [text, setText] = useState('');
  const [description, setDescription] = useState('');
  const [level, setLevel] = useState('');

  // How many questions of each type (0 = type not included)
  const [counts, setCounts] = useState({
    reading: 0,
    grammar: 0,
    vocabulary: 0,
    truefalse: 0,
  });

  // The generated text (Unseen mode only)
  const [passageTitle, setPassageTitle] = useState('');
  const [passage, setPassage] = useState('');

  const [questions, setQuestions] = useState('');
  const [answerKey, setAnswerKey] = useState('');

  // loading indicator while AI generates
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isGenerating) return;

    const sections = QUIZ_TYPES
      .filter((t) => counts[t] > 0)
      .map((t) => ({ quizType: t, count: counts[t] }));
    const total = sections.reduce((sum, s) => sum + s.count, 0);

    if (total < 1 || total > MAX_TOTAL) {
      alert(`Please choose between 1 and ${MAX_TOTAL} questions in total.`);
      return;
    }

    setIsGenerating(true);
    try {
      const levelCode = (level || '').split(' ')[0]; // A1/A2/B1/B2/C1/C2

      let url;
      let payload;
      if (mode === 'unseen') {
        url = 'http://127.0.0.1:8000/api/unseen/create';
        payload = { description, level: levelCode, sections };
      } else {
        url = 'http://127.0.0.1:8000/api/quizzes/create';
        payload = { source_text: text, level: levelCode, sections };
      }

      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      // Unseen: { title, passage, result }   Paste: { result }
      const parts = splitQuiz(data.result);
      setQuestions(parts.questions);
      setAnswerKey(parts.answerKey);

      if (mode === 'unseen') {
        setPassageTitle(data.title || '');
        setPassage(data.passage || '');
      } else {
        setPassageTitle('');
        setPassage('');
      }
    } catch (err) {
      console.error('Generate failed:', err);
      setQuestions(`ERROR: ${err.message}`);
      setAnswerKey('');
      setPassageTitle('');
      setPassage('');
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
          mode={mode} setMode={setMode}
          text={text} setText={setText}
          description={description} setDescription={setDescription}
          level={level} setLevel={setLevel}
          counts={counts} setCounts={setCounts}
        />

        <GenerateButton isLoading={isGenerating} />

        {isGenerating && (
          <div className="ai-loading" role="status" aria-live="polite">
            <span className="ai-loading__spinner" aria-hidden="true"></span>
            <div className="ai-loading__text">
              <div className="ai-loading__title">
                {mode === 'unseen'
                  ? 'AI is writing the text and preparing your quiz…'
                  : 'AI is preparing your quiz…'}
              </div>
              <div className="ai-loading__subtitle">
                {mode === 'unseen'
                  ? 'This can take a little longer than usual.'
                  : 'Please wait a few seconds.'}
              </div>
            </div>
          </div>
        )}
      </form>

      {(questions || answerKey) && (
        <>
          <QuizResult
            passageTitle={passageTitle}
            passage={passage}
            onChangePassage={setPassage}
            questions={questions}
            answerKey={answerKey}
            onChangeQuestions={setQuestions}
            onChangeAnswerKey={setAnswerKey}
          />
          <QuizChat onSendMessage={handleChatMessage} />
          <DownloadDocxButton
            content={combinedForDownload}
            passage={passage}
            passageTitle={passageTitle}
          />
        </>
      )}
    </div>
  );
}

export default App;