import React from "react";

export default function DownloadDocxButton({ content }) {
  const handleDownload = async () => {
    try {
      // שליחת התוכן לשרת כדי שיווצר DOCX תקין ומעוצב
      const res = await fetch("http://127.0.0.1:8000/api/quizzes/export/docx", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,          // כל הטקסט של התרגיל
          filename: "quiz", // שם הקובץ ללא סיומת
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      // קבלת הקובץ כ־Blob והורדה אוטומטית למחשב
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "quiz.docx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
      alert("Download failed: " + err.message);
    }
  };

  return (
    <button type="button" onClick={handleDownload}>
      📥 Download as DOCX
    </button>
  );
}
