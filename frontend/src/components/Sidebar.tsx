import React, { useEffect, useState } from 'react';
import styled from 'styled-components';

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

  // Function to add new log entry (can be triggered as needed)
  const addLogEntry = (emoji: string, message: string) => {
    setLog([...log, { emoji, message }]);
  };

  // Simulate a new task being added after 5 seconds
  useEffect(() => {
    const timeout = setTimeout(() => {
      addLogEntry('🚀', 'Processing new data...');
    }, 5000);

    return () => clearTimeout(timeout);
  }, []);


  return (
    <SidebarContainer>
      <LogTitle>AI Agent Tasks</LogTitle>
      {log.map((item, index) => (
        <MenuItem key={index}>
          <span>{item.emoji}</span>
          {item.message}
        </MenuItem>
      ))}
    </SidebarContainer>
  );
};
