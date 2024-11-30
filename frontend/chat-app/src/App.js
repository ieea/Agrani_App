import React, { useState } from 'react';

const App = () => {
  const [name, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [followup, setFollowUp] = useState([]); // State for follow-up questions
  

  const handleQueryChange = (e) => {
    setQuery(e.target.value);
  };

  const handleButtonClick = async () => {
    try {
      const apiResponse = await fetch('http://0.0.0.0:3500/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ name }),
      });

      if (!apiResponse.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await apiResponse.json();
      const { response, followup } = data;
      setResponse(response); // Assuming the API returns { response: "your_response" }
      setFollowUp(followup);    
    } catch (error) {
      setResponse(`Error: ${error.message}`);
    }
  };

  return (
    <div>
      <h1>Query Form</h1>
      <form onSubmit={(e) => e.preventDefault()}>
        <label>
          Query:
          <input type="text" value={name} onChange={handleQueryChange} />
        </label>
        <button type="button" onClick={handleButtonClick}>Submit</button>
      </form>
      <h2>Response:</h2>
      <p>{response}</p>
      {followup.length > 0 && (
        <div>
          <h3>Follow-Up Questions:</h3>
          <ul>
            {followup.map((question, index) => (
              <li key={index}>{question}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default App;