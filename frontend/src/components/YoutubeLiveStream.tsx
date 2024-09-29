import React, { useState, useEffect } from 'react';
import Draggable from 'react-draggable';
import styled from 'styled-components';
import { startProcessingWithYouTubeLink, getHeadlines } from '../utils/VideoService'; // Import service functions
import { DataGrid } from './DataGrid'; // Import DataGrid to display headlines

const PlayerContainer = styled.div<{ minimized: boolean }>`
  position: fixed;
  bottom: ${props => (props.minimized ? '20px' : '20px')};
  right: ${props => (props.minimized ? '20px' : '20px')};
  width: ${props => (props.minimized ? '200px' : '400px')};
  height: ${props => (props.minimized ? '150px' : '300px')};
  background-color: #000;
  z-index: 1000;
  transition: width 0.3s ease, height 0.3s ease;
  overflow: hidden;
  border: 1px solid #00ff00;
`;

const Controls = styled.div`
  display: flex;
  justify-content: space-between;
  background-color: #000;
  padding: 5px;
`;

const ControlButton = styled.button`
  background: none;
  border: none;
  color: #00ff00;
  cursor: pointer;
  font-size: 14px;
`;

const ChannelSelector = styled.select`
  background-color: #000;
  color: #00ff00;
  border: 1px solid #00ff00;
  margin-right: 5px;
`;

export const YouTubeLiveStream: React.FC = () => {
  const [minimized, setMinimized] = useState(false);
  const [channelId, setChannelId] = useState('YWqrC6FaURA'); // Default channel ID
  const [visible, setVisible] = useState(true);
  const [headlines, setHeadlines] = useState<string[]>([]); // State to hold fetched headlines
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Function to start processing with selected YouTube channel
  const startProcessing = async (youtubeUrl: string) => {
    try {
      setLoading(true);
      await startProcessingWithYouTubeLink(youtubeUrl);
      setLoading(false);
    } catch (error: any) {
      setError(error.message);
      setLoading(false);
    }
  };

  // Function to fetch headlines in intervals
  useEffect(() => {
    const fetchHeadlinesPeriodically = async () => {
      try {
        const headlines = await getHeadlines();
        console.log(headlines)
        setHeadlines(headlines);
      } catch (error: any) {
        setError(error.message);
      }
    };

    // Start fetching headlines every 10 seconds
    const intervalId = setInterval(fetchHeadlinesPeriodically, 5000);

    // Clear interval on unmount
    return () => clearInterval(intervalId);
  }, []);

  // When channel changes, start the processing with new channel
  useEffect(() => {
    console.log(channelId)
    const youtubeUrl = channelId;
    startProcessing(youtubeUrl); 
  }, [channelId]); 

  const handleMinimize = () => {
    setMinimized(!minimized);
  };

  const handleClose = () => {
    setVisible(false);
  };

  const handleChannelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setChannelId(e.target.value);
  };

  if (!visible) return null;

  return (
    <div>
      <Draggable>
        <PlayerContainer minimized={minimized}>
          <Controls>
            <div>
              {!minimized && (
                <ChannelSelector onChange={handleChannelChange} value={channelId}>
                  <option value="UC4R8DWoMoI7CAwX8_LjQHig">YouTube Live</option>
                  <option value="UCYO_jab_esuFRV4b17AJtAw">NASA Live</option>
                  <option value="UCsT0YIqwnpJCM-mx7-gSA4Q">TED Talks</option>
                  {/* Add more channels as needed */}
                </ChannelSelector>
              )}
            </div>
            <div>
              <ControlButton onClick={handleMinimize}>
                {minimized ? '🔼' : '🔽'}
              </ControlButton>
              <ControlButton onClick={handleClose}>❌</ControlButton>
            </div>
          </Controls>
          {!minimized && (
            <iframe
              width="100%"
              height="100%"
              src={`https://www.youtube.com/embed/${channelId}?autoplay=1`}
              frameBorder="0"
              allow="autoplay; encrypted-media"
              allowFullScreen
              title="Live Stream"
            ></iframe>
          )}
        </PlayerContainer>
      </Draggable>

      {/* Display headlines fetched from API */}
      {loading && <div>Loading headlines...</div>}
      {error && <div>Error: {error}</div>}
      {headlines.length > 0 && (
        <div>
          <h3>Headlines</h3>
          <DataGrid /> 
        </div>
      )}
    </div>
  );
};
