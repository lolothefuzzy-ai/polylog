/**
 * API Setup for Tests
 * Ensures API server is running and accessible
 */

export async function ensureApiRunning(page) {
  const maxRetries = 30;
  const retryDelay = 1000; // 1 second
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await page.request.get('http://localhost:8000/health');
      if (response.ok()) {
        return true;
      }
    } catch (error) {
      // API not ready yet
    }
    
    await page.waitForTimeout(retryDelay);
  }
  
  throw new Error('API server did not become ready within timeout');
}

export async function testTier0Endpoint(page, endpoint, method = 'GET', data = null) {
  const url = `http://localhost:8000${endpoint}`;
  
  try {
    let response;
    if (method === 'GET') {
      response = await page.request.get(url);
    } else if (method === 'POST') {
      response = await page.request.post(url, { data });
    } else {
      throw new Error(`Unsupported method: ${method}`);
    }
    
    return {
      ok: response.ok(),
      status: response.status(),
      data: response.ok() ? await response.json() : null
    };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      error: error.message,
      data: null
    };
  }
}

