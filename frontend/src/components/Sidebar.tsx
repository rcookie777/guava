import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { getAgentStatus } from '../utils/VideoService'; // Import the getAgentStatus function

const SidebarContainer = styled.div`
  width: 200px;
  background-color: #1e1e1e;
  padding: 20px;
  color: #cfcfcf;
  height: 100vh;
  overflow-y: auto;
`;

const MenuItem = styled.div`
  margin-bottom: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 0.9rem;

  &:hover {
    color: #ffffff;
  }

  span {
    margin-right: 10px;
    font-size: 1.5rem;
  }
`;

const LogTitle = styled.h2`
  color: #ffffff;
  margin-bottom: 20px;
  font-size: 1.2rem;
`;

interface LogItem {
  emoji: string;
  message: string;
}

export const Sidebar: React.FC = () => {
  const [log, setLog] = useState<LogItem[]>([
    { emoji: '🤖', message: 'Initializing AI agent...' },
    { emoji: '🧠', message: 'Analyzing data...' },
    { emoji: '🔍', message: 'Searching for relevant information...' }
  ]);

  // Function to add new log entry
  const addLogEntry = (emoji: string, message: string) => {
    setLog([...log, { emoji, message }]);
  };

  // Periodically fetch agent status
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const status = await getAgentStatus(); // Get agent status from server
        addLogEntry('🔄', status.progress); // Log the progress
      } catch (error) {
        console.error('Error fetching agent status:', error);
      }
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <SidebarContainer>
      <LogTitle>Task Manager</LogTitle>
      {log.map((item, index) => (
        <MenuItem key={index}>
          <span>{item.emoji}</span>
          {item.message}
        </MenuItem>
      ))}
    </SidebarContainer>
  );
};
