import React, { useState } from 'react';
import Statistics from './Statistics';
import TopicChat from './TopicChat';
import './App.css';


function App() {
  // Add state for page navigation
  const [currentPage, setCurrentPage] = useState('chat');

  const renderCurrentPage = () => {
    switch(currentPage) {
      case 'statistics':
        return <Statistics />;
      case 'chat':
      default:
        return (
          <main className="right-chat-area">
            <TopicChat />
          </main>
        );
    }
  };




  return (
    <div className="page-wrapper-with-background">
      <header className="app-header-simple">
        <h1>🎯 Posture Manager</h1>
        <p className="header-subtitle">AI-Powered Posture Monitoring & Improvement</p>
      </header>

      <div className="main-layout-container">
        <aside className="left-content-area">
          <div className="user-welcome">
            <h2>👋 Welcome back!</h2>
            <p>Track your posture journey</p>
          </div>
          
          <div className="nav-menu">
            <button 
              className={`nav-button ${currentPage === 'chat' ? 'active' : ''}`}
              onClick={() => setCurrentPage('chat')}
            >
              <span className="nav-icon">🤖</span>
              <div className="nav-content">
                <span className="nav-title">PosturAI Assistant</span>
                <span className="nav-subtitle">Topic-based guidance</span>
              </div>
            </button>
            <button 
              className={`nav-button ${currentPage === 'statistics' ? 'active' : ''}`}
              onClick={() => setCurrentPage('statistics')}
            >
              <span className="nav-icon">📊</span>
              <div className="nav-content">
                <span className="nav-title">Statistics & Trends</span>
                <span className="nav-subtitle">View your progress</span>
              </div>
            </button>
          </div>
          
          <div className="user-info">
            <h3>📈 Today's Overview</h3>
            <div className="quick-stat">
              <div className="stat-info">
                <span className="stat-label">Monitoring Time</span>
                <span className="stat-value">4.2h</span>
              </div>
              <div className="stat-icon">⏱️</div>
            </div>
            <div className="quick-stat">
              <div className="stat-info">
                <span className="stat-label">Good Posture</span>
                <span className="stat-value good">78%</span>
              </div>
              <div className="stat-icon">✅</div>
            </div>
            <div className="quick-stat">
              <div className="stat-info">
                <span className="stat-label">Alerts Today</span>
                <span className="stat-value alert">12</span>
              </div>
              <div className="stat-icon">⚠️</div>
            </div>
          </div>

          <div className="quick-actions">
            <h3>🚀 Quick Actions</h3>
            <button className="action-btn">
              <span>📊</span>
              Analyze Today's Data
            </button>
            <button className="action-btn">
              <span>🎯</span>
              Set Posture Goal
            </button>
          </div>
        </aside>

        {renderCurrentPage()}
      </div>
    </div>
  );
}

export default App;