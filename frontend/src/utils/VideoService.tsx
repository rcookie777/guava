import React, { useState } from 'react';

// Service function to start processing with a YouTube link
export const startProcessingWithYouTubeLink = async (youtubeUrl: string) => {
  try {
    const response = await fetch(`http://localhost:8080/start?youtube_url=${encodeURIComponent(youtubeUrl)}`, {
      method: 'GET',
    });
    if (!response.ok) {
      throw new Error('Failed to start processing');
    }
    const data = await response.json();
    console.log('Processing started:', data);
    return data;
  } catch (error) {
    console.error('Error starting processing:', error);
    throw error;
  }
};

export const getHeadlines = async () => {
  try {
    const response = await fetch('http://localhost:8080/get_headlines', {
      method: 'GET',
    });
    if (!response.ok) {
      throw new Error('Failed to fetch headlines');
    }
    const headlines = await response.json();
    return headlines;
  } catch (error) {
    console.error('Error fetching headlines:', error);
    throw error;
  }
};

export const runAgent = async (marketHeader: string) => {
    try {
      const response = await fetch('http://localhost:8080/start_agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ market_header: marketHeader }),
      });
      if (!response.ok) {
        throw new Error('Failed to start agent');
      }
      const data = await response.json();
      console.log('Agent started:', data);
      return data;
    } catch (error) {
      console.error('Error starting agent:', error);
      throw error;
    }
  };
  
  export const getAgentStatus = async () => {
    try {
      const response = await fetch('http://localhost:8080/agent_status', {
        method: 'GET',
      });
      if (!response.ok) {
        throw new Error('Failed to fetch agent status');
      }
      const status = await response.json();
      return status;
    } catch (error) {
      console.error('Error fetching agent status:', error);
      throw error;
    }
  };
  
