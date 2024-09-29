import React from 'react';
import styled from 'styled-components';
import { DataGrid } from './DataGrid';

const ContentContainer = styled.div`
  flex: 1;
  padding: 20px;
  background-color: #000;
`;

export const ContentArea: React.FC = () => {
  return (
    <ContentContainer>
      <DataGrid />
    </ContentContainer>
  );
};
