export function splitQuiz(text) {
  if (!text) return { questions: "", answerKey: "" };

  const lines = text.replace(/\r\n/g, "\n").split("\n");

  // Auxiliary function: Markdown marker cleaner and format
  const normalize = (s) =>
    s
      .trim()
      .replace(/[*_`~#>]/g, "")     
      .replace(/\s+/g, " ")          
      .toLowerCase();

  let idx = -1;
  for (let i = 0; i < lines.length; i++) {
    const norm = normalize(lines[i]);
    if (norm === "answer key" || norm === "answer key:" ) {
      idx = i;
      break;
    }
  }

  if (idx === -1) {
    return { questions: text.trim(), answerKey: "" };
  }

  const questions = lines.slice(0, idx).join("\n").trim();
  const answerKey = lines.slice(idx + 1).join("\n").trim();
  return { questions, answerKey };
}

export function joinQuiz(questions, answerKey) {
  const q = (questions || "").trim();
  const a = (answerKey || "").trim();
  if (!a) return q;
  return `${q}\n\nANSWER KEY\n${a}`;
}
