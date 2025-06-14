import React, { useState, useEffect, useRef } from 'react';
import Statistics from './Statistics';
import './App.css';

const FLASK_BACKEND_URL = 'http://localhost:5000';

function App() {
  // Add state for page navigation
  const [currentPage, setCurrentPage] = useState('chat');
  
  // --- Chat State and Logic ---
  const [messageInput, setMessageInput] = useState('');
  const [messageList, setMessageList] = useState([
    { id: 1, text: "Hi! I'm PosturAI. How can I help you with your posture today?", sender: "ai" }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messageList]);

  const handleSendMessage = async () => {
    if (!messageInput.trim()) return;
    setIsLoading(true);

    const newUserMessage = { id: Date.now(), text: messageInput, sender: "user" };
    setMessageList(prevMessages => [...prevMessages, newUserMessage]);
    const currentQuestion = messageInput;
    setMessageInput('');

    try {
      const response = await fetch(`${FLASK_BACKEND_URL}/chat_ai`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: currentQuestion }),
      });
      setIsLoading(false);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ reply: `Error from server: ${response.status}` }));
        throw new Error(errorData.reply || `HTTP Error: ${response.status}`);
      }
      const data = await response.json();
      const newAiMessage = { id: Date.now() + 1, text: data.reply, sender: "ai" };
      setMessageList(prevMessages => [...prevMessages, newAiMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      setIsLoading(false);
      const errorMessageForAI = { id: Date.now() + 1, text: error.message || "Oops, something went wrong. Please try again.", sender: "ai" };
      setMessageList(prevMessages => [...prevMessages, errorMessageForAI]);
    }
  };

  const renderCurrentPage = () => {
    switch(currentPage) {
      case 'statistics':
        return <Statistics />;
      case 'chat':
      default:
        return (
          <main className="right-chat-area">
            <div className="chat-container">
              <div className="chat-header">
                <h2>Chat with PosturAI</h2>
              </div>
              <div className="messages-list">
                {messageList.map(msg => (
                  <div key={msg.id} className={`message ${msg.sender === 'user' ? 'user-message' : 'ai-message'}`}>
                    {msg.text}
                  </div>
                ))}
                {isLoading && (
                  <div className="message ai-message loading-message">
                    <em>PosturAI is thinking...</em>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              <div className="input-area">
                <input
                  type="text"
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleSendMessage()}
                  placeholder="Ask me about posture..."
                  disabled={isLoading}
                />
                <button onClick={handleSendMessage} disabled={isLoading}>
                  {isLoading ? 'Sending...' : 'Send'}
                </button>
              </div>
            </div>
          </main>
        );
    }
  };

  return (
    <div className="page-wrapper-with-background">
      <header className="app-header-simple">
        <h1>Posture Manager</h1>
      </header>

      <div className="main-layout-container">
        <aside className="left-content-area">
          <h2>Navigation</h2>
          <div className="nav-menu">
            <button 
              className={`nav-button ${currentPage === 'chat' ? 'active' : ''}`}
              onClick={() => setCurrentPage('chat')}
            >
              <span className="nav-icon">💬</span>
              Chat with PosturAI
            </button>
            <button 
              className={`nav-button ${currentPage === 'statistics' ? 'active' : ''}`}
              onClick={() => setCurrentPage('statistics')}
            >
              <span className="nav-icon">📊</span>
              Statistics & Graphs
            </button>
          </div>
          
          <div className="user-info">
            <h3>Quick Stats</h3>
            <div className="quick-stat">
              <span>Today's Monitoring:</span>
              <span className="stat-value">4.2h</span>
            </div>
            <div className="quick-stat">
              <span>Good Posture:</span>
              <span className="stat-value good">78%</span>
            </div>
            <div className="quick-stat">
              <span>Alerts Today:</span>
              <span className="stat-value alert">12</span>
            </div>
          </div>
        </aside>

        {currentPage === 'statistics' ? <Statistics /> : renderCurrentPage()}
      </div>
    </div>
  );
}

export default App;