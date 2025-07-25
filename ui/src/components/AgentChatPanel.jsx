import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { buildApiUrl } from '../api';
import useLivePrices from '../hooks/useLivePrices';

const AgentChatPanel = () => {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [detectedSymbols, setDetectedSymbols] = useState([]);
  const { prices, connectionStatus } = useLivePrices(detectedSymbols);

  // Extract ticker symbols from question
  const extractSymbols = (text) => {
    const symbolPattern = /\b[A-Z]{1,5}\b/g;
    return text.match(symbolPattern) || [];
  };

  const generateMockAgentResponse = (question) => {
    const lowerQuestion = question.toLowerCase();
    const symbols = extractSymbols(question);
    const symbol = symbols[0] || 'the stock';
    
    if (lowerQuestion.includes('buy') || lowerQuestion.includes('should i')) {
      return {
        message: `Based on current market analysis, ${symbol} shows mixed signals. Consider technical indicators like RSI, MACD, and volume before making investment decisions. This is a demo response - connect to live backend for real-time analysis.`,
        recommendation: 'WAIT',
        confidence: 0.6
      };
    }
    
    if (lowerQuestion.includes('price') || lowerQuestion.includes('target')) {
      return {
        message: `${symbol} is currently trading with moderate volatility. Key support and resistance levels should be monitored. This is a demo response - connect to live backend for real-time price analysis.`,
        recommendation: 'MONITOR',
        confidence: 0.5
      };
    }
    
    if (lowerQuestion.includes('technical') || lowerQuestion.includes('analysis')) {
      return {
        message: `Technical analysis for ${symbol} suggests reviewing multiple timeframes and indicators. RSI, MACD, and moving averages provide comprehensive insights. This is a demo response - connect to live backend for detailed technical analysis.`,
        recommendation: 'ANALYZE',
        confidence: 0.7
      };
    }
    
    // Default response
    return {
      message: `I understand you're asking about ${symbol}. While I'm currently running in demo mode, I can help analyze stocks, provide technical insights, and suggest trading strategies. Connect to the live backend for real-time market analysis.`,
      recommendation: 'DEMO_MODE',
      confidence: 0.5
    };
  };

  useEffect(() => {
    const symbols = extractSymbols(question);
    setDetectedSymbols(symbols);
  }, [question]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    const userMessage = { type: 'user', content: question, timestamp: new Date() };
    setChatHistory(prev => [...prev, userMessage]);

    try {
      const response = await axios.post(buildApiUrl('/api/agent'), { question });
      const agentMessage = { 
        type: 'agent', 
        content: response.data, 
        timestamp: new Date(),
        symbols: extractSymbols(question)
      };
      setChatHistory(prev => [...prev, agentMessage]);
      setResponse(response.data);
    } catch (error) {
      console.error('Agent API error:', error);
      
      // Show backend connection required message
      setChatHistory(prev => [...prev, 
        { type: 'user', content: question },
        { type: 'agent', 
          content: {
            message: 'Backend connection required for live agent analysis. Please ensure your backend server is running and accessible.',
            recommendation: 'BACKEND_REQUIRED',
            confidence: 0
          }, 
          timestamp: new Date().toLocaleTimeString() 
        }
      ]);
    }
    setLoading(false);
    setQuestion('');
  };

  const formatPrice = (price) => {
    if (price === null || price === undefined) return '—';
    return typeof price === 'number' ? price.toFixed(2) : price;
  };

  const formatTimestamp = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return '';
    }
  };

  return (
    <div>
      <h2>Agent Chat</h2>
      
      {/* Live Price Context */}
      {detectedSymbols.length > 0 && (
        <div style={{
          marginBottom: '15px',
          padding: '10px',
          backgroundColor: '#f8f9fa',
          borderRadius: '5px',
          border: '1px solid #dee2e6'
        }}>
          <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '8px' }}>
            Live Context ({connectionStatus}):
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
            {detectedSymbols.map(symbol => {
              const livePrice = prices[symbol];
              return (
                <div key={symbol} style={{
                  padding: '4px 8px',
                  backgroundColor: 'white',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  fontSize: '13px'
                }}>
                  <strong>{symbol}</strong>: ${formatPrice(livePrice?.price)}
                  {livePrice?.timestamp && (
                    <div style={{ fontSize: '11px', color: '#666' }}>
                      {formatTimestamp(livePrice.timestamp)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Chat History */}
      <div style={{
        maxHeight: '400px',
        overflowY: 'auto',
        marginBottom: '15px',
        border: '1px solid #ddd',
        borderRadius: '5px',
        padding: '10px'
      }}>
        {chatHistory.length === 0 ? (
          <div style={{ color: '#666', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
            Ask me about any stock! I'll provide real-time analysis.
          </div>
        ) : (
          chatHistory.map((message, idx) => (
            <div key={idx} style={{
              marginBottom: '15px',
              padding: '10px',
              backgroundColor: message.type === 'user' ? '#e3f2fd' : '#f5f5f5',
              borderRadius: '8px',
              borderLeft: `4px solid ${message.type === 'user' ? '#2196f3' : '#4caf50'}`
            }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
                {message.type === 'user' ? 'You' : 'Agent'} • {formatTimestamp(message.timestamp)}
              </div>
              
              {message.type === 'user' ? (
                <div>{message.content}</div>
              ) : message.content.error ? (
                <div style={{ color: 'red' }}>Error: {message.content.error}</div>
              ) : (
                <div>
                  <div style={{ marginBottom: '8px' }}>
                    <span style={{
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      fontWeight: 'bold',
                      backgroundColor:
                        message.content.decision === 'buy' ? 'var(--accent-secondary)' :
                        message.content.decision === 'sell' ? 'var(--accent-danger)' : 'var(--bg-tertiary)',
                      color: 'var(--text-primary)'
                    }}>
                      {message.content.decision?.toUpperCase() || 'WAIT'}
                    </span>
                    <span style={{ marginLeft: '10px', fontSize: '14px' }}>
                      Confidence: {message.content.confidence || 0}
                    </span>
                  </div>
                  <div>{message.content.explanation}</div>
                </div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div style={{
            padding: '10px',
            backgroundColor: '#f5f5f5',
            borderRadius: '8px',
            borderLeft: '4px solid #4caf50',
            fontStyle: 'italic',
            color: '#666'
          }}>
            Agent is thinking...
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit}>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            placeholder="Ask about any stock (e.g., 'Should I buy AAPL now?')"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            style={{ 
              flex: 1, 
              padding: '12px', 
              border: '1px solid #ddd',
              borderRadius: '5px',
              fontSize: '14px'
            }}
          />
          <button 
            type="submit" 
            disabled={loading || !question.trim()}
            style={{
              padding: '12px 20px',
              backgroundColor: loading ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: 'bold'
            }}
          >
            {loading ? 'Thinking...' : 'ASK'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AgentChatPanel;
