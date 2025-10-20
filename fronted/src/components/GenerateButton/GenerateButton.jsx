import React from 'react';

function GenerateButton() {
  return (
    <button
      type="submit"
      style={{
        width: '100%',
        padding: '15px',
        fontSize: '16px',
        backgroundColor: '#4CAF50',
        color: 'white',
        border: 'none',
        borderRadius: '5px',
        cursor: 'pointer'
      }}
    >
      ⚡ Generate Quiz
    </button>
  );
}

export default GenerateButton;
