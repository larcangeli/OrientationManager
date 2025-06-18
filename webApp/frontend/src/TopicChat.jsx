import React, { useState, useEffect, useRef } from 'react';
import './TopicChat.css';

const FLASK_BACKEND_URL = 'http://localhost:5000';

const POSTURE_TOPICS = [
  {
    id: 'analysis',
    title: 'Posture Analysis',
    icon: '📊',
    description: 'Review your current posture data and trends',
    color: '#3498db',
    questions: [
      'How is my posture today?',
      'What are my main posture issues?',
      'Show me my posture trends this week',
      'When do I have the worst posture?'
    ]
  },
  {
    id: 'tips',
    title: 'Improvement Tips',
    icon: '💡',
    description: 'Get personalized posture improvement advice',
    color: '#f39c12',
    questions: [
      'How can I improve my posture?',
      'What should I focus on first?',
      'Give me quick posture fixes',
      'What habits should I change?'
    ]
  },
  {
    id: 'exercises',
    title: 'Exercise Recommendations',
    icon: '🏃',
    description: 'Specific exercises for your detected issues',
    color: '#e74c3c',
    questions: [
      'What exercises can help my posture?',
      'Show me desk exercises I can do',
      'Exercises for forward head posture',
      'Quick stretches for better posture'
    ]
  },
  {
    id: 'workspace',
    title: 'Workspace Setup',
    icon: '🪑',
    description: 'Optimize your desk and chair configuration',
    color: '#9b59b6',
    questions: [
      'How should I set up my desk?',
      'What\'s the ideal monitor height?',
      'Chair adjustment recommendations',
      'Ergonomic workspace tips'
    ]
  },
  {
    id: 'breaks',
    title: 'Break Reminders',
    icon: '⏰',
    description: 'Optimal break timing and activities',
    color: '#1abc9c',
    questions: [
      'How often should I take breaks?',
      'What should I do during breaks?',
      'Best break activities for posture',
      'How to make breaks more effective?'
    ]
  },
  {
    id: 'progress',
    title: 'Progress Tracking',
    icon: '📈',
    description: 'Understand your posture improvement over time',
    color: '#27ae60',
    questions: [
      'Am I improving over time?',
      'What progress have I made?',
      'Set posture improvement goals',
      'Compare this week to last week'
    ]
  }
];

// Add markdown parsing for better formatting
const formatMessage = (text) => {
    // Simple markdown-like parsing
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
      .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
      .replace(/`(.*?)`/g, '<code>$1</code>') // Code
      .replace(/\n/g, '<br>'); // Line breaks
  };

function TopicChat() {
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleTopicSelect = (topic) => {
    setSelectedTopic(topic);
    setMessages([
      {
        id: Date.now(),
        text: `Hi! I'm PosturAI. I'm here to help you with ${topic.title.toLowerCase()}. Choose a question below or ask me anything about this topic!`,
        sender: 'ai',
        topic: topic.id
      }
    ]);
  };

  const handleQuestionSelect = async (question) => {
    await sendMessage(question);
  };

  const sendMessage = async (messageText) => {
    if (!messageText.trim() || !selectedTopic) return;
    
    setIsLoading(true);
    
    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user'
    };
    
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`${FLASK_BACKEND_URL}/chat_ai`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: messageText,
          topic: selectedTopic.id,
          context: `Topic: ${selectedTopic.title} - ${selectedTopic.description}`
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }

      const data = await response.json();
      const aiMessage = {
        id: Date.now() + 1,
        text: data.reply,
        sender: 'ai',
        topic: selectedTopic.id
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage = {
        id: Date.now() + 1,
        text: "Sorry, I'm having trouble responding right now. Please try again.",
        sender: 'ai'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToTopics = () => {
    setSelectedTopic(null);
    setMessages([]);
  };

  if (!selectedTopic) {
    return (
      <div className="topic-selection">
        <div className="topic-header">
          <h2>🎯 Choose Your Posture Topic</h2>
          <p>Select a topic to get personalized advice from PosturAI</p>
        </div>
        
        <div className="topics-grid">
          {POSTURE_TOPICS.map(topic => (
            <div
              key={topic.id}
              className="topic-card"
              onClick={() => handleTopicSelect(topic)}
              style={{ '--topic-color': topic.color }}
            >
              <div className="topic-icon">{topic.icon}</div>
              <h3>{topic.title}</h3>
              <p>{topic.description}</p>
              <div className="topic-arrow">→</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="topic-chat-container">
      <div className="topic-chat-header">
        <button className="back-button" onClick={handleBackToTopics}>
          ← Back to Topics
        </button>
        <div className="current-topic">
          <span className="topic-icon">{selectedTopic.icon}</span>
          <span className="topic-title">{selectedTopic.title}</span>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.sender}-message`}>
            {msg.text}
          </div>
        ))}
        {isLoading && (
          <div className="message ai-message loading">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <em>PosturAI is thinking...</em>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="quick-questions">
        <h4>Quick Questions:</h4>
        <div className="question-buttons">
          {selectedTopic.questions.map((question, index) => (
            <button
              key={index}
              className="question-btn"
              onClick={() => handleQuestionSelect(question)}
              disabled={isLoading}
            >
              {question}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TopicChat;