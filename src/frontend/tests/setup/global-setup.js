/**
 * Global Test Setup
 * Checks that servers are running before tests start
 */

async function globalSetup(config) {
  console.log('[Test Setup] Checking servers...');
  
  const checkServer = async (url, name) => {
    try {
      const response = await fetch(url);
      if (response.ok) {
        console.log(`[Test Setup] ✓ ${name} server is running`);
        return true;
      } else {
        console.log(`[Test Setup] ✗ ${name} server returned ${response.status}`);
        return false;
      }
    } catch (error) {
      console.log(`[Test Setup] ✗ ${name} server not accessible: ${error.message}`);
      return false;
    }
  };
  
  const apiRunning = await checkServer('http://localhost:8000/health', 'API');
  const frontendRunning = await checkServer('http://localhost:5173', 'Frontend');
  
  if (!apiRunning || !frontendRunning) {
    console.log('\n[Test Setup] WARNING: Servers not running!');
    console.log('[Test Setup] Start servers with: python scripts/dev.py');
    console.log('[Test Setup] Tests may fail if servers are not available.\n');
  } else {
    console.log('[Test Setup] All servers ready!\n');
  }
}

module.exports = globalSetup;

