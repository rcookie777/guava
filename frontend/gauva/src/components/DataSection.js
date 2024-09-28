import React from 'react';
import { Typography, List, ListItem, ListItemText } from '@mui/material';

function DataSection() {
  // Sample data
  const dataItems = [
    { name: 'Market A', value: 'Up 2%' },
    { name: 'Market B', value: 'Down 1%' },
    // Add more data items as needed
  ];

  return (
    <div>
      <Typography variant="h6" gutterBottom>
        Data Section
      </Typography>
      <List>
        {dataItems.map((item, index) => (
          <ListItem key={index} divider>
            <ListItemText primary={item.name} secondary={item.value} />
          </ListItem>
        ))}
      </List>
    </div>
  );
}

export default DataSection;

