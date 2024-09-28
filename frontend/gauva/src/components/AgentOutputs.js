import React from 'react';
import { Typography, List, ListItem, ListItemText } from '@mui/material';

function AgentOutputs() {
  // Sample tasks and outputs
  const agentTasks = [
    { task: 'Analyze Market A', status: 'Completed' },
    { task: 'Predict Market B', status: 'In Progress' },
    // Add more tasks as needed
  ];

  return (
    <div>
      <Typography variant="h6" gutterBottom>
        Agent Outputs & Tasks
      </Typography>
      <List>
        {agentTasks.map((item, index) => (
          <ListItem key={index} divider>
            <ListItemText primary={item.task} secondary={item.status} />
          </ListItem>
        ))}
      </List>
    </div>
  );
}

export default AgentOutputs;

