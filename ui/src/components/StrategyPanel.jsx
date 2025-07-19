import React from 'react';
import { Box, Typography, Paper, Button, TextField, Grid, CircularProgress } from '@mui/material';
import axios from 'axios';
import { apiUrl } from '../api';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function StrategyPanel() {
  const [symbol, setSymbol] = React.useState('AAPL');
  const [params, setParams] = React.useState({ ema_length: 20, rsi_thresh: 30 });
  const [result, setResult] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  const runSimulation = () => {
    setLoading(true);
    axios.post(apiUrl('/api/simulate'), { symbol, params }).then(res => {
      setResult(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>Strategy Testing</Typography>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField label="Symbol" value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())} fullWidth />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField label="EMA Length" type="number" value={params.ema_length} onChange={e => setParams(p => ({ ...p, ema_length: Number(e.target.value) }))} fullWidth />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField label="RSI Threshold" type="number" value={params.rsi_thresh} onChange={e => setParams(p => ({ ...p, rsi_thresh: Number(e.target.value) }))} fullWidth />
          </Grid>
          <Grid item xs={12} md={4}>
            <Button variant="contained" onClick={runSimulation} disabled={loading} fullWidth>Run Simulation</Button>
          </Grid>
        </Grid>
      </Paper>
      {loading && <Box textAlign="center"><CircularProgress /></Box>}
      {result && (
        <Box>
          <Typography variant="subtitle1">Performance:</Typography>
          <ul>
            <li>Total Return: {result.performance.total_return}</li>
            <li>Win Rate: {result.performance.win_rate}</li>
            <li>Max Drawdown: {result.performance.max_drawdown}</li>
            <li>Number of Trades: {result.performance.n_trades}</li>
          </ul>
          <Typography variant="subtitle1">Equity Curve:</Typography>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={result.equity_curve.map((y, i) => ({ x: i, y }))}>
              <XAxis dataKey="x" hide />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="y" stroke="#1976d2" dot={false} name="Equity" />
            </LineChart>
          </ResponsiveContainer>
          <Typography variant="subtitle1">Trade Log:</Typography>
          <Paper sx={{ maxHeight: 200, overflow: 'auto', p: 1 }}>
            <pre style={{ margin: 0, fontSize: 12 }}>{JSON.stringify(result.trade_log, null, 2)}</pre>
          </Paper>
        </Box>
      )}
    </Box>
  );
}
