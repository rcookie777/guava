import React from 'react';
import styled from 'styled-components';

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  color: #00ff00;
`;

const TableHeader = styled.th`
  border-bottom: 1px solid #555;
  padding: 10px;
  text-align: left;
`;

const TableCell = styled.td`
  border-bottom: 1px solid #333;
  padding: 10px;
`;

const data = [
  { symbol: 'AAPL', price: 150.12, change: '+1.25%' },
  { symbol: 'GOOG', price: 2729.89, change: '-0.85%' },
  { symbol: 'AMZN', price: 3342.88, change: '+0.15%' },
];

export const DataGrid: React.FC = () => {
  return (
    <Table>
      <thead>
        <tr>
          <TableHeader>Symbol</TableHeader>
          <TableHeader>Price</TableHeader>
          <TableHeader>Change</TableHeader>
        </tr>
      </thead>
      <tbody>
        {data.map((item) => (
          <tr key={item.symbol}>
            <TableCell>{item.symbol}</TableCell>
            <TableCell>{item.price}</TableCell>
            <TableCell>{item.change}</TableCell>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};
