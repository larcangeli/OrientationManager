import React, { useState, useEffect, useRef } from 'react';
import './App.css'; // We'll heavily modify this

// Assume FLASK_BACKEND_URL is still relevant if you're calling an API for the chat
const FLASK_BACKEND_URL = 'http://localhost:5000';

function App() {
  // --- Chat State and Logic (Keep this as it was) ---
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
  // --- End Chat State and Logic ---

  return (
    <div className="page-wrapper-with-background"> {/* For the overall page background */}
      <header className="app-header-simple"> {/* Optional: A simple header */}
        <h1>Posture Manager</h1>
      </header>

      <div className="main-layout-container"> {/* This will be our flex container */}
        <aside className="left-content-area">
          <h2>Left Area</h2>
          <p>This space can be used for other components, navigation, or information later.</p>
          {/* Example: You could later import and place components here like:
            <UserProfile />
            <QuickLinks />
          */}
        </aside>

        <main className="right-chat-area">
          {/* The existing chat-container and its content go here */}
          <div className="chat-container">
            <div className="chat-header"> {/* Re-using chat-header style for consistency */}
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
      </div>
      {/* Optional: A simple footer
      <footer className="app-footer-simple">
        <p>&copy; {new Date().getFullYear()} PosturAI. User: {larcangeli}</p>
      </footer>
      */}
    </div>
  );
}

export default App;