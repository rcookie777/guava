// api.ts
export const getHeadlines = async (): Promise<string[]> => {
    const response = await fetch('http://localhost:8080/get_headlines');
    if (!response.ok) throw new Error('Failed to fetch headlines');
    return response.json();
  };
  
  export const startAgentForHeadline = async (headline: string) => {
    const response = await fetch('http://localhost:8080/start_agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ market_header: headline })
    });
    if (!response.ok) throw new Error('Failed to start agent for headline');
    return response.json();
  };
  