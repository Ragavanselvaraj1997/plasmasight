import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, Zap, Layers, AlertTriangle } from 'lucide-react';

const Dashboard = () => {
  const [data, setData] = useState([]);
  const [currentMetrics, setCurrentMetrics] = useState({
    predicted_depth: 0,
    rf_power: 0,
    status: 'Initializing'
  });

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8001/ws/metrics');

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setCurrentMetrics(message);

      setData(prev => {
        const newData = [...prev, message];
        if (newData.length > 50) newData.shift();
        return newData;
      });
    };

    return () => ws.close();
  }, []);

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Plasma Etch Control System</h1>
        <div className="status-badge">
          <span className={`status-dot ${currentMetrics.status === 'Running' ? 'green' : 'red'}`}></span>
          {currentMetrics.status}
        </div>
      </header>

      <div className="metrics-grid">
        <div className="metric-card">
          <Layers className="icon" />
          <div className="metric-info">
            <h3>Predicted Depth</h3>
            <p>{currentMetrics.predicted_depth?.toFixed(3)} µm</p>
          </div>
        </div>
        <div className="metric-card">
          <Zap className="icon" />
          <div className="metric-info">
            <h3>RF Power</h3>
            <p>{currentMetrics.rf_power?.toFixed(1)} W</p>
          </div>
        </div>
        <div className="metric-card">
          <Activity className="icon" />
          <div className="metric-info">
            <h3>System Health</h3>
            <p>Optimal</p>
          </div>
        </div>
      </div>

      <div className="charts-container">
        <div className="chart-wrapper">
          <h2>Etch Depth Trajectory</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="timestamp" tick={false} />
              <YAxis domain={['auto', 'auto']} stroke="#ccc" />
              <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', border: 'none' }} />
              <Legend />
              <Line type="monotone" dataKey="predicted_depth" stroke="#00d2ff" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-wrapper">
          <h2>RF Power Stability</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="timestamp" tick={false} />
              <YAxis domain={['auto', 'auto']} stroke="#ccc" />
              <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', border: 'none' }} />
              <Legend />
              <Line type="monotone" dataKey="rf_power" stroke="#ff4d4d" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
