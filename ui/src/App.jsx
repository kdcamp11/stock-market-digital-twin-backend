import React from 'react';
import { CssBaseline, AppBar, Toolbar, Typography, Box, Tabs, Tab } from '@mui/material';
import DashboardPanel from './components/DashboardPanel';
import AlertsPanel from './components/AlertsPanel';
import StrategyPanel from './components/StrategyPanel';
import AgentChatPanel from './components/AgentChatPanel';
import TechnicalAnalysisPanel from './components/TechnicalAnalysisPanel';

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
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
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
      >
        <Tab label="Live Dashboard" {...a11yProps(0)} />
        <Tab label="Alerts Log" {...a11yProps(1)} />
        <Tab label="Strategy Testing" {...a11yProps(2)} />
        <Tab label="Agent Chat" {...a11yProps(3)} />
        <Tab label="Technical Analysis" {...a11yProps(4)} />
      </Tabs>
      <TabPanel value={tab} index={0}>
        <DashboardPanel />
      </TabPanel>
      <TabPanel value={tab} index={1}>
        <AlertsPanel />
      </TabPanel>
      <TabPanel value={tab} index={2}>
        <StrategyPanel />
      </TabPanel>
      <TabPanel value={tab} index={3}>
        <AgentChatPanel />
      </TabPanel>
      <TabPanel value={tab} index={4}>
        <TechnicalAnalysisPanel />
      </TabPanel>
    </Box>
  );
}
