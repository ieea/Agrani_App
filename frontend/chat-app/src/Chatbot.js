import React, { useState } from 'react';
import axios from 'axios';
import './Chatbot.css'; // Import styles

const Chatbot = () => {
  const [name, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [followUpQuestions, setFollowUpQuestions] = useState([]);

  const handleQueryChange = (e) => {
    setQuery(e.target.value);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    const userMessage = { sender: 'user', text: name };
    setMessages([...messages, userMessage]);
    setQuery('');

    try {
      const response = await axios.post('http://0.0.0.0:3500/run', { name });
      const botMessage = { sender: 'bot', text: response.data.response };
      setMessages((prevMessages) => [...prevMessages, userMessage, botMessage]);

      // Update follow-up questions
      setFollowUpQuestions(response.data['follow up'] || []);
    } catch (error) {
      const errorMessage = { sender: 'bot', text: 'Error: Unable to get response from the server' };
      setMessages((prevMessages) => [...prevMessages, userMessage, errorMessage]);
    }
  };

  const handleFollowUpClick = async (question) => {
    const userMessage = { sender: 'user', text: question };
    setMessages([...messages, userMessage]);

    try {
      const response = await axios.post('http://0.0.0.0:3500/run', { name: question });
      const botMessage = { sender: 'bot', text: response.data.response };
      setMessages((prevMessages) => [...prevMessages, userMessage, botMessage]);

      // Update follow-up questions
      setFollowUpQuestions(response.data['follow up'] || []);
    } catch (error) {
      const errorMessage = { sender: 'bot', text: 'Error: Unable to get response from the server' };
      setMessages((prevMessages) => [...prevMessages, userMessage, errorMessage]);
    }
  };

  return (
    <div className="chatbot">
      <h1>Chatbot</h1>
      <div className="chatbox">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.sender}`}>
            <p><strong>{message.sender}:</strong> {message.text}</p>
          </div>
        ))}
      </div>
      <form onSubmit={handleFormSubmit}>
        <input
          type="text"
          value={name}
          onChange={handleQueryChange}
          placeholder="Ask me something..."
        />
        <button type="submit">Send</button>
      </form>
      {followUpQuestions.length > 0 && (
        <div className="follow-up">
          <h3>Follow-Up Questions:</h3>
          <ul>
            {followUpQuestions.map((question, index) => (
              <li key={index} onClick={() => handleFollowUpClick(question)}>{question}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default Chatbot;
