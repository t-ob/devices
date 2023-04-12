import React, { useEffect, useState } from 'react';
import './App.css';

interface Device {
  ip_address: string;
  mac_address: string;
  last_seen: string;
}

function formatDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}


const App: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);

  useEffect(() => {
    fetchDevices(true);

    const intervalId = setInterval(() => {
      fetchDevices(false);
    }, 60 * 1000);

    return () => {
      clearInterval(intervalId);
    };
  }, []);

  async function fetchDevices(fromDatabase: boolean = false) {
    try {
      const baseUrl = '/scan';
      const searchParams = new URLSearchParams();
      searchParams.append('from_database', fromDatabase.toString());

      const response = await fetch(`${baseUrl}?${searchParams.toString()}`);
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      const { devices } = await response.json();
      console.log({ devices });
      setDevices(devices);
      setLastRefreshedAt(new Date());
    } catch (error) {
      console.error('Error fetching devices:', error);
    }
  }

  async function sendWakeOnLAN(macAddress: string) {
    try {
      const response = await fetch('/wake', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mac_address: macAddress }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        alert('Wake-on-LAN packet sent.');
      } else {
        alert(`Error sending Wake-on-LAN packet: ${result.message}`);
      }
    } catch (error) {
      console.error('Error sending Wake-on-LAN packet:', error);
      alert(`Error sending Wake-on-LAN packet: ${error}`);
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl mb-4">Network Devices</h1>
      {lastRefreshedAt && (
        <p className="text-sm mb-4">
          Last refreshed at: {formatDate(lastRefreshedAt)}
        </p>
      )}
      <table className="table-auto">
        <thead>
          <tr>
            <th className="border px-4 py-2">IP Address</th>
            <th className="border px-4 py-2">MAC Address</th>
            <th className="border px-4 py-2">Last Seen</th>
            <th className="border px-4 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((device, index) => (
            <tr key={index} className={index % 2 === 0 ? 'bg-gray-100' : ''}>
              <td className="border px-4 py-2">{device.ip_address}</td>
              <td className="border px-4 py-2">{device.mac_address}</td>
              <td className="border px-4 py-2">{formatDate(new Date(device.last_seen))}</td>
              <td className="border px-4 py-2">
                <button
                  onClick={() => sendWakeOnLAN(device.mac_address)}
                  className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                >
                  Wake on LAN
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default App;
