import React from 'react';
import styled from 'styled-components';
import { TopBar } from './TopBar';
import { ContentArea } from './ContentArea';
import { YouTubeLiveStream } from './YoutubeLiveStream';

const MainContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
`;

export const MainContent: React.FC = () => {
  return (
    <MainContainer>
      <TopBar />
      <ContentArea />
      <YouTubeLiveStream />
    </MainContainer>
  );
};
