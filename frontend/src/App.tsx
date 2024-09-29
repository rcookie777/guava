import React from 'react';
import styled from 'styled-components';
import { Sidebar } from './components/Sidebar';
import { MainContent } from './components/MainContent';

const AppContainer = styled.div`
  display: flex;
  height: 100vh;
  background-color: #000; /* Black background */
  color: #00ff00; /* Green text */
`;

const App: React.FC = () => {
  return (
    <AppContainer>
      <Sidebar />
      <MainContent />
    </AppContainer>
  );
};

export default App;
