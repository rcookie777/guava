import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark', // Dark mode
    primary: {
      main: '#00ff00', // Green text like Bloomberg
    },
    background: {
      default: '#000000', // Black background
      paper: '#1a1a1a',   // Dark grey panels
    },
  },
  typography: {
    fontFamily: 'Monospace', // Monospaced font
  },
});

export default theme;

