import React from 'react';
import { CssBaseline, AppBar, Toolbar, Typography, Box, Tabs, Tab } from '@mui/material';
import DashboardPanel from './components/DashboardPanel';
import EnhancedDashboard from './components/EnhancedDashboard';
import AlertsPanel from './components/AlertsPanel';
import AgentChatPanel from './components/AgentChatPanel';

function a11yProps(index) {
  return {
    id: `main-tab-${index}`,
    'aria-controls': `tabpanel-${index}`,
  };
}

function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`main-tab-${index}`}
      className="tab-panel"
      {...other}
    >
      {value === index && children}
    </div>
  );
}

export default function App() {
  const [tab, setTab] = React.useState(0);
  return (
    <Box sx={{ flexGrow: 1 }}>
      <CssBaseline />
      <AppBar position="static" sx={{ backgroundColor: 'var(--bg-secondary)', boxShadow: 'none', borderBottom: '1px solid var(--border-primary)' }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, color: 'var(--text-primary)', fontFamily: 'Inter, sans-serif', fontWeight: 600 }}>
            Stock Market Digital Twin
          </Typography>
        </Toolbar>
      </AppBar>
      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        indicatorColor="primary"
        textColor="inherit"
        variant="scrollable"
        scrollButtons="auto"
        aria-label="Main Tabs"
        sx={{
          backgroundColor: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-primary)',
          '& .MuiTab-root': {
            color: 'var(--text-secondary)',
            fontFamily: 'Inter, sans-serif',
            fontWeight: 500,
            textTransform: 'none',
            fontSize: '14px',
            '&.Mui-selected': {
              color: 'var(--text-primary)'
            },
            '&:hover': {
              color: 'var(--text-primary)',
              backgroundColor: 'var(--bg-tertiary)'
            }
          },
          '& .MuiTabs-indicator': {
            backgroundColor: 'var(--accent-primary)'
          }
        }}
      >
        <Tab label="Live Dashboard" {...a11yProps(0)} />
        <Tab label="Alerts Log" {...a11yProps(1)} />
      </Tabs>
      <TabPanel value={tab} index={0}>
        <EnhancedDashboard />
      </TabPanel>
      <TabPanel value={tab} index={1}>
        <AlertsPanel />
      </TabPanel>
    </Box>
  );
}
