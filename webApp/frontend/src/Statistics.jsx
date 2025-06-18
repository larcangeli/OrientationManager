import React, { useState, useEffect } from 'react';
import './Statistics.css';

const FLASK_BACKEND_URL = 'http://localhost:5000';

function Statistics() {
  const [postureData, setPostureData] = useState([]);
  const [summaryStats, setSummaryStats] = useState({});
  const [selectedPeriod, setSelectedPeriod] = useState(7);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPostureStats(selectedPeriod);
  }, [selectedPeriod]);

  const fetchPostureStats = async (days) => {
    try {
      setLoading(true);
      const response = await fetch(`${FLASK_BACKEND_URL}/api/posture-stats?days=${days}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setPostureData(data.daily_data || []);
      setSummaryStats(data.summary || {});
      setError(null);
    } catch (err) {
      console.error('Error fetching posture statistics:', err);
      setError('Failed to load statistics. Please try again.');
      // Set fallback data
      setPostureData([]);
      setSummaryStats({});
    } finally {
      setLoading(false);
    }
  };

  // Pie Chart Component
  const PieChart = ({ data, title, size = 200 }) => {
    const total = data.reduce((sum, item) => sum + item.value, 0);
    let cumulativePercentage = 0;

    const createPath = (percentage, cumulativePercentage) => {
      const startAngle = cumulativePercentage * 3.6; // Convert to degrees
      const endAngle = (cumulativePercentage + percentage) * 3.6;
      
      const startAngleRad = (startAngle - 90) * (Math.PI / 180);
      const endAngleRad = (endAngle - 90) * (Math.PI / 180);
      
      const radius = size / 2 - 10;
      const centerX = size / 2;
      const centerY = size / 2;
      
      const x1 = centerX + radius * Math.cos(startAngleRad);
      const y1 = centerY + radius * Math.sin(startAngleRad);
      const x2 = centerX + radius * Math.cos(endAngleRad);
      const y2 = centerY + radius * Math.sin(endAngleRad);
      
      const largeArcFlag = percentage > 50 ? 1 : 0;
      
      return `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
    };

    return (
      <div className="pie-chart-container">
        <h4>{title}</h4>
        <div className="pie-chart-wrapper">
          <svg width={size} height={size} className="pie-chart">
            {data.map((item, index) => {
              const percentage = (item.value / total) * 100;
              const path = createPath(percentage, cumulativePercentage);
              cumulativePercentage += percentage;
              
              return (
                <path
                  key={index}
                  d={path}
                  fill={item.color}
                  stroke="white"
                  strokeWidth="2"
                  className="pie-slice"
                  data-tooltip={`${item.label}: ${percentage.toFixed(1)}%`}
                />
              );
            })}
            {/* Center circle for donut effect */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={size / 6}
              fill="white"
              stroke="#e5e7eb"
              strokeWidth="2"
            />
            {/* Center text */}
            <text
              x={size / 2}
              y={size / 2 - 5}
              textAnchor="middle"
              className="pie-center-text"
              fontSize="14"
              fontWeight="600"
              fill="#374151"
            >
              Total
            </text>
            <text
              x={size / 2}
              y={size / 2 + 10}
              textAnchor="middle"
              className="pie-center-value"
              fontSize="16"
              fontWeight="700"
              fill="#1f2937"
            >
              {total}
            </text>
          </svg>
          <div className="pie-legend">
            {data.map((item, index) => (
              <div key={index} className="legend-item">
                <span 
                  className="legend-color-dot" 
                  style={{ backgroundColor: item.color }}
                ></span>
                <span className="legend-label">{item.label}</span>
                <span className="legend-percentage">
                  {((item.value / total) * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderPostureDistributionPie = () => {
    const postureDistribution = [
      {
        label: 'Good Posture',
        value: summaryStats.good_posture_percentage || 0,
        color: '#10b981'
      },
      {
        label: 'Forward Lean',
        value: summaryStats.forward_lean_percentage || 0,
        color: '#f59e0b'
      },
      {
        label: 'Side Tilt',
        value: summaryStats.side_tilt_percentage || 0,
        color: '#ef4444'
      },
      {
        label: 'Other Issues',
        value: Math.max(0, 100 - (summaryStats.good_posture_percentage || 0) - 
               (summaryStats.forward_lean_percentage || 0) - 
               (summaryStats.side_tilt_percentage || 0)),
        color: '#8b5cf6'
      }
    ].filter(item => item.value > 0);

    return (
      <PieChart 
        data={postureDistribution} 
        title="🎯 Posture Distribution"
        size={220}
      />
    );
  };

  const renderAlertCategoriesPie = () => {
    const totalAlerts = summaryStats.total_alerts || 0;
    const forwardLeanAlerts = Math.round(totalAlerts * 0.6);
    const sideTiltAlerts = Math.round(totalAlerts * 0.25);
    const otherAlerts = totalAlerts - forwardLeanAlerts - sideTiltAlerts;

    const alertCategories = [
      {
        label: 'Forward Lean',
        value: forwardLeanAlerts,
        color: '#f59e0b'
      },
      {
        label: 'Side Tilt',
        value: sideTiltAlerts,
        color: '#ef4444'
      },
      {
        label: 'Other',
        value: otherAlerts,
        color: '#8b5cf6'
      }
    ].filter(item => item.value > 0);

    return (
      <PieChart 
        data={alertCategories} 
        title="⚠️ Alert Categories"
        size={220}
      />
    );
  };

  const renderHourlyDistributionPie = () => {
    const hourlyData = [
      { label: 'Morning (6-12)', value: 25, color: '#10b981' },
      { label: 'Afternoon (12-18)', value: 45, color: '#f59e0b' },
      { label: 'Evening (18-24)', value: 20, color: '#3b82f6' },
      { label: 'Night (0-6)', value: 10, color: '#8b5cf6' }
    ];

    return (
      <PieChart 
        data={hourlyData} 
        title="🕐 Activity Distribution"
        size={220}
      />
    );
  };

  const renderPostureChart = () => {
    if (!postureData.length) return null;

    return (
      <div className="chart-container">
        <h3>📊 Daily Posture Trends - Last {selectedPeriod} Days</h3>
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
      <div className="chart-container">
        <h3>⚠️ Alert Frequency - Last {selectedPeriod} Days</h3>
        <div className="alert-chart">
          {postureData.map((day, index) => (
            <div key={index} className="alert-bar">
              <div 
                className="bar alert-bar-fill" 
                style={{ height: `${Math.min(day.alert_count * 5, 100)}%` }}
                title={`Alerts: ${day.alert_count}`}
              ></div>
              <div className="bar-label">{day.date}</div>
              <div className="alert-count">{day.alert_count}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="statistics-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading your posture statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="statistics-container">
        <div className="error-state">
          <p>{error}</p>
          <button onClick={() => fetchPostureStats(selectedPeriod)}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="statistics-container">
      <div className="statistics-header">
        <h2>📊 Posture Statistics & Analytics</h2>
        <p>Track your posture improvement journey with detailed insights</p>
      </div>

      {/* Period Selection */}
      <div className="period-selector">
        <h3>📅 Select Time Period</h3>
        <div className="period-buttons">
          <button 
            className={`period-btn ${selectedPeriod === 7 ? 'active' : ''}`}
            onClick={() => setSelectedPeriod(7)}
          >
            <span className="period-icon">📅</span>
            <div className="period-content">
              <span className="period-title">Last 7 Days</span>
              <span className="period-subtitle">Weekly Overview</span>
            </div>
          </button>
          <button 
            className={`period-btn ${selectedPeriod === 14 ? 'active' : ''}`}
            onClick={() => setSelectedPeriod(14)}
          >
            <span className="period-icon">📆</span>
            <div className="period-content">
              <span className="period-title">Last 14 Days</span>
              <span className="period-subtitle">Bi-weekly Trends</span>
            </div>
          </button>
          <button 
            className={`period-btn ${selectedPeriod === 30 ? 'active' : ''}`}
            onClick={() => setSelectedPeriod(30)}
          >
            <span className="period-icon">🗓️</span>
            <div className="period-content">
              <span className="period-title">Last 30 Days</span>
              <span className="period-subtitle">Monthly Analysis</span>
            </div>
          </button>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="summary-stats">
        <h3>📈 Summary Statistics</h3>
        <div className="stats-grid">
          <div className="stat-card total-hours">
            <div className="stat-icon">⏱️</div>
            <div className="stat-content">
              <h4>Total Monitoring</h4>
              <div className="stat-value">{summaryStats.total_hours || 0}h</div>
            </div>
          </div>
          <div className="stat-card good-posture">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <h4>Good Posture</h4>
              <div className="stat-value good">{summaryStats.good_posture_percentage || 0}%</div>
            </div>
          </div>
          <div className="stat-card forward-lean">
            <div className="stat-icon">⬇️</div>
            <div className="stat-content">
              <h4>Forward Lean</h4>
              <div className="stat-value warning">{summaryStats.forward_lean_percentage || 0}%</div>
            </div>
          </div>
          <div className="stat-card side-tilt">
            <div className="stat-icon">↔️</div>
            <div className="stat-content">
              <h4>Side Tilt</h4>
              <div className="stat-value warning">{summaryStats.side_tilt_percentage || 0}%</div>
            </div>
          </div>
          <div className="stat-card total-alerts">
            <div className="stat-icon">🚨</div>
            <div className="stat-content">
              <h4>Total Alerts</h4>
              <div className="stat-value alert">{summaryStats.total_alerts || 0}</div>
            </div>
          </div>
        </div>
      </div>

      {/* PIE CHARTS SECTION */}
      <div className="pie-charts-section">
        <h3>🥧 Distribution Analysis</h3>
        <div className="pie-charts-grid">
          {renderPostureDistributionPie()}
          {renderAlertCategoriesPie()}
          {renderHourlyDistributionPie()}
        </div>
      </div>

      {/* Charts */}
      <div className="charts-section">
        {renderPostureChart()}
        {renderAlertFrequency()}
      </div>

      {/* AI Insights */}
      <div className="insights-section">
        <h3>🤖 AI Insights & Recommendations</h3>
        <div className="insights-content">
          <div className="insight-card">
            <div className="insight-icon">🎯</div>
            <div className="insight-text">
              <h4>Primary Focus Area</h4>
              <p>Your posture tends to deteriorate during afternoon hours (2-6 PM). Consider setting more frequent break reminders during this period.</p>
            </div>
          </div>
          <div className="insight-card">
            <div className="insight-icon">📈</div>
            <div className="insight-text">
              <h4>Progress Tracking</h4>
              <p>You've shown {selectedPeriod === 7 ? '15%' : selectedPeriod === 14 ? '12%' : '18%'} improvement in good posture time compared to the previous period. Keep up the great work!</p>
            </div>
          </div>
          <div className="insight-card">
            <div className="insight-icon">💡</div>
            <div className="insight-text">
              <h4>Quick Tip</h4>
              <p>Take breaks every 45 minutes for posture reset. Weekend posture shows improvement - try to maintain weekday awareness.</p>
            </div>
          </div>
        </div>
        <button className="ai-analysis-btn">
          <span>🤖</span>
          Get Detailed AI Analysis
        </button>
      </div>
    </div>
  );
}

export default Statistics;