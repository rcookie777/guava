import React from 'react';
import styled from 'styled-components';

const TopBarContainer = styled.div`
  height: 50px;
  background-color: #333;
  display: flex;
  align-items: center;
  padding: 0 15px;
`;

const CommandInput = styled.input`
  width: 100%;
  background: none;
  border: none;
  color: #00ff00;
  font-size: 16px;
  outline: none;
`;

export const TopBar: React.FC = () => {
  return (
    <TopBarContainer>
      <CommandInput placeholder="Enter command..." />
    </TopBarContainer>
  );
};
