import React, { useState, useEffect } from 'react';
import './App.css';
import DeviceDetail from './DeviceDetail';

function DeviceList() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDevice, setSelectedDevice] = useState(null);

  useEffect(() => {
    // Fetch devices from the backend API
    // Ensure the backend API is running and accessible
    // Adjust the URL if the backend is running elsewhere
    const apiUrl = '/api/devices/'; // Using relative path for proxy (needs setup) or direct URL

    fetch(apiUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        setDevices(data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching devices:", error);
        setError(error.message);
        setLoading(false);
      });
  }, []); // Empty dependency array means this effect runs once on mount

  const handleDeviceClick = (device) => {
    setSelectedDevice(device);
  };

  const handleCloseDetail = () => {
    setSelectedDevice(null);
  };

  if (loading) {
    return <div>Loading devices...</div>;
  }

  if (error) {
    return <div>Error loading devices: {error}. Make sure the backend API is running and accessible.</div>;
  }

  return (
    <div className="device-list">
      <h2>Discovered Devices</h2>
      {devices.length === 0 ? (
        <p>No devices found yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>IP Address</th>
              <th>MAC Address</th>
              <th>Type</th>
              <th>OS</th>
              <th>Status</th>
              <th>Last Seen</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {devices.map(device => (
              <tr key={device.id} className="device-row">
                <td>{device.id}</td>
                <td>{device.name || 'N/A'}</td>
                <td>{device.ip_address}</td>
                <td>{device.mac_address || 'N/A'}</td>
                <td>{device.device_type}</td>
                <td>{device.os || 'N/A'}</td>
                <td>{device.status}</td>
                <td>{new Date(device.last_seen).toLocaleString()}</td>
                <td>
                  <button 
                    className="view-details-button"
                    onClick={() => handleDeviceClick(device)}
                  >
                    Ver Detalhes
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      
      {selectedDevice && (
        <DeviceDetail 
          device={selectedDevice} 
          onClose={handleCloseDetail} 
        />
      )}
    </div>
  );
}

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Hardware Inventory Dashboard</h1>
      </header>
      <main>
        <DeviceList />
      </main>
      <footer>
        <p>Inventory System v0.2</p>
      </footer>
    </div>
  );
}

export default App;
