import React from 'react';
import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, CircularProgress } from '@mui/material';
import axios from 'axios';
import { apiUrl } from '../api';

export default function AlertsPanel() {
  const [loading, setLoading] = React.useState(true);
  const [alerts, setAlerts] = React.useState([]);

  React.useEffect(() => {
    axios.get(apiUrl('/api/alerts/log')).then(res => {
      setAlerts(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <Box textAlign="center"><CircularProgress /></Box>;
  if (!alerts.length) return <Typography>No alerts found.</Typography>;

  return (
    <Box>
      <Typography variant="h6" gutterBottom>Alerts Log</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>Symbol</TableCell>
              <TableCell>Rule</TableCell>
              <TableCell>Summary</TableCell>
              <TableCell>Confidence</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {alerts.map((alert, idx) => (
              <TableRow key={idx}>
                <TableCell>{alert.timestamp}</TableCell>
                <TableCell>{alert.symbol}</TableCell>
                <TableCell>{alert.rule}</TableCell>
                <TableCell>{alert.summary}</TableCell>
                <TableCell>{alert.confidence}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
