import React from 'react';
import styled from 'styled-components';

const SidebarContainer = styled.div`
  width: 200px;
  background-color: #1e1e1e;
  padding: 20px;
`;

const MenuItem = styled.div`
  margin-bottom: 15px;
  cursor: pointer;
  &:hover {
    color: #ffffff;
  }
`;

export const Sidebar: React.FC = () => {
  return (
    <SidebarContainer>
      <MenuItem>Market Data</MenuItem>
      <MenuItem>News</MenuItem>
      <MenuItem>Portfolio</MenuItem>
      <MenuItem>Settings</MenuItem>
    </SidebarContainer>
  );
};
