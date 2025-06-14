import React, { useState, useEffect } from 'react';
import './Statistics.css';

const Statistics = () => {
  const [postureData, setPostureData] = useState([]);
  const [summaryStats, setSummaryStats] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7'); // days

  useEffect(() => {
    fetchPostureData();
  }, [timeRange]);

  const fetchPostureData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/api/posture-stats?days=${timeRange}`);
      const data = await response.json();
      setPostureData(data.daily_data || []);
      setSummaryStats(data.summary || {});
    } catch (error) {
      console.error('Error fetching posture data:', error);
    }
    setIsLoading(false);
  };

  const renderPostureChart = () => {
    if (!postureData.length) return <div>No data available</div>;

    return (
      <div className="chart-container">
        <h3>Daily Posture Trends</h3>
        <div className="simple-chart">
          {postureData.map((day, index) => (
            <div key={index} className="chart-bar">
              <div 
                className="bar good-posture" 
                style={{ height: `${day.good_posture_percentage}%` }}
                title={`Good Posture: ${day.good_posture_percentage}%`}
              ></div>
              <div 
                className="bar poor-posture" 
                style={{ height: `${day.poor_posture_percentage}%` }}
                title={`Poor Posture: ${day.poor_posture_percentage}%`}
              ></div>
              <div className="bar-label">{day.date}</div>
            </div>
          ))}
        </div>
        <div className="chart-legend">
          <span className="legend-item">
            <span className="legend-color good"></span>Good Posture
          </span>
          <span className="legend-item">
            <span className="legend-color poor"></span>Poor Posture
          </span>
        </div>
      </div>
    );
  };

  const renderAlertFrequency = () => {
    if (!postureData.length) return null;

    return (
      <div className="alert-frequency">
        <h3>Alert Frequency</h3>
        <div className="frequency-grid">
          {postureData.map((day, index) => (
            <div key={index} className="frequency-item">
              <div className="frequency-date">{day.date}</div>
              <div className="frequency-count">{day.alert_count} alerts</div>
              <div className="frequency-bar">
                <div 
                  className="frequency-fill" 
                  style={{ width: `${(day.alert_count / 50) * 100}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="statistics-container">
      <div className="stats-header">
        <h1>Posture Statistics</h1>
        <div className="time-range-selector">
          <label>Time Range: </label>
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value)}
          >
            <option value="7">Last 7 days</option>
            <option value="14">Last 14 days</option>
            <option value="30">Last 30 days</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="loading">Loading statistics...</div>
      ) : (
        <>
          <div className="summary-cards">
            <div className="stat-card">
              <h3>Total Monitor Time</h3>
              <div className="stat-value">{summaryStats.total_hours || 0}h</div>
            </div>
            <div className="stat-card">
              <h3>Good Posture</h3>
              <div className="stat-value good">{summaryStats.good_posture_percentage || 0}%</div>
            </div>
            <div className="stat-card">
              <h3>Forward Lean</h3>
              <div className="stat-value warning">{summaryStats.forward_lean_percentage || 0}%</div>
            </div>
            <div className="stat-card">
              <h3>Side Tilt</h3>
              <div className="stat-value warning">{summaryStats.side_tilt_percentage || 0}%</div>
            </div>
            <div className="stat-card">
              <h3>Total Alerts</h3>
              <div className="stat-value alert">{summaryStats.total_alerts || 0}</div>
            </div>
          </div>

          {renderPostureChart()}
          {renderAlertFrequency()}

          <div className="insights-section">
            <h3>AI Insights & Recommendations</h3>
            <div className="insights-content">
              <p>Based on your posture data analysis:</p>
              <ul>
                <li>Your posture tends to deteriorate during afternoon hours (2-6 PM)</li>
                <li>Consider taking breaks every 45 minutes for posture reset</li>
                <li>Weekend posture shows improvement - try to maintain weekday awareness</li>
                <li>Forward leaning is your primary concern - check monitor height</li>
              </ul>
              <button className="ai-analysis-btn">Get Detailed AI Analysis</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Statistics;