import React, { useState } from 'react';
import Draggable from 'react-draggable';
import styled from 'styled-components';

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
  const [channelId, setChannelId] = useState('UC4R8DWoMoI7CAwX8_LjQHig'); // Default channel ID
  const [visible, setVisible] = useState(true);

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
            src={`https://www.youtube.com/embed/live_stream?channel=${channelId}&autoplay=1`}
            frameBorder="0"
            allow="autoplay; encrypted-media"
            allowFullScreen
            title="Live Stream"
          ></iframe>
        )}
      </PlayerContainer>
    </Draggable>
  );
};
