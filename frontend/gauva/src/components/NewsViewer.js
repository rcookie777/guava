import React from 'react';
import { Typography, List, ListItem, ListItemText, Link } from '@mui/material';

function NewsViewer() {
  // Sample news items
  const newsItems = [
    { title: 'Market A Hits Record High', url: '#' },
    { title: 'Economic Outlook for Q4', url: '#' },
    // Add more news items as needed
  ];

  return (
    <div>
      <Typography variant="h6" gutterBottom>
        Current News
      </Typography>
      <List>
        {newsItems.map((item, index) => (
          <ListItem key={index} divider>
            <ListItemText
              primary={
                <Link href={item.url} target="_blank" rel="noopener">
                  {item.title}
                </Link>
              }
            />
          </ListItem>
        ))}
      </List>
    </div>
  );
}

export default NewsViewer;

