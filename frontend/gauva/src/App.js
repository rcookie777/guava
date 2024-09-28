import React from 'react';
import { Grid, Paper } from '@mui/material';
import DataSection from './components/DataSection';
import AgentOutputs from './components/AgentOutputs';
import NewsViewer from './components/NewsViewer';

function App() {
  return (
    <Grid container spacing={2} style={{ padding: 20 }}>
      {/* Data Section */}
      <Grid item xs={12} md={4}>
        <Paper style={{ height: '100%', padding: 20 }}>
          <DataSection />
        </Paper>
      </Grid>

      {/* Agent Outputs and Tasks */}
      <Grid item xs={12} md={4}>
        <Paper style={{ height: '100%', padding: 20 }}>
          <AgentOutputs />
        </Paper>
      </Grid>

      {/* News Viewer */}
      <Grid item xs={12} md={4}>
        <Paper style={{ height: '100%', padding: 20 }}>
          <NewsViewer />
        </Paper>
      </Grid>
    </Grid>
  );
}

export default App;

