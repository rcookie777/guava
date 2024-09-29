import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { getHeadlines } from '../utils/VideoService';  // Import the service for fetching headlines

// Styled components for the table
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

// Wrapper for scrolling
const ScrollContainer = styled.div`
  max-height: 300px;  // Limit height to allow scrolling
  overflow-y: auto;   // Enable vertical scrolling
`;

// TypeScript interface for headline data (adjust to your structure)
interface HeadlineData {
  symbol: string;
  price: number | null;  // Initialize with null as placeholder
  venue: string | null;  // Initialize with null as placeholder
}

export const DataGrid: React.FC = () => {
  const [data, setData] = useState<HeadlineData[]>([]);  // State to hold the fetched headlines
  const [loading, setLoading] = useState<boolean>(true); // State to show loading status
  const [error, setError] = useState<string | null>(null); // State to hold any error

  // Function to fetch and append new headlines
  const fetchAndAppendHeadlines = async () => {
    try {
      const headlines = await getHeadlines();  // Fetch new headlines, which only contain the `symbol` field
      // Map the fetched symbols to include placeholders for `price` and `change`
      const updatedData = headlines.map((headline: string) => ({
        symbol: headline,
        price: null,  // Initialize with null or 0.00 until price is available
        venue: null  // Initialize with null or "N/A" until change is available
      }));
      setData((prevData) => [...prevData, ...updatedData]); // Append new headlines to the existing ones
      setLoading(false);
    } catch (error: any) {
      setError(error.message);
      setLoading(false);
    }
  };

  // UseEffect to fetch headlines periodically and update the table
  useEffect(() => {
    const intervalId = setInterval(fetchAndAppendHeadlines, 5000); // Fetch every 5 seconds
    return () => clearInterval(intervalId);  // Clean up the interval on unmount
  }, []);  // Empty dependency array ensures the effect runs once after mount

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  // Render the table with fetched data
  return (
    <ScrollContainer>
      <Table>
        <thead>
          <tr>
            <TableHeader>Symbol</TableHeader>
            <TableHeader>Price</TableHeader>
            <TableHeader>Venue</TableHeader>
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => (
            <tr key={index}>
              <TableCell>{item.symbol}</TableCell>
              <TableCell>{item.price !== null ? item.price.toFixed(2) : '0.00'}</TableCell> 
              <TableCell>{item.venue !== null ? item.venue : 'Polymarket'}</TableCell> 
            </tr>
          ))}
        </tbody>
      </Table>
    </ScrollContainer>
  );
};
