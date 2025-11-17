import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Polylog6 visual and integration testing
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests',
  
  /* Run tests in files in parallel */
  /* Disabled for single window - use workers=1 instead */
  fullyParallel: false,
  
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  
  /* Single worker to ensure one browser window */
  workers: 1,
  
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html'],
    ['list'],
    process.env.CI ? ['github'] : ['list']
  ],
  
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173',
    
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
    
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Video on failure */
    video: 'retain-on-failure',
  },

        /* Configure projects for major browsers */
        projects: [
          {
            name: 'chromium',
            use: { 
              ...devices['Desktop Chrome'],
              headless: false, // Always show browser
              viewport: { width: 1280, height: 720 },
              // Reuse browser context to keep single window
              channel: 'chrome', // Use installed Chrome for better single-window support
            },
          },

    /* Test against mobile viewports. */
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },
  ],

  /* Run your local dev server before starting the tests */
  /* DISABLED - servers must be started separately using unified_single_window_test.py */
  /* This prevents multiple window launches */
  // webServer: [
  //   {
  //     command: 'python ../../scripts/dev.py',
  //     url: 'http://localhost:5173',
  //     reuseExistingServer: !process.env.CI,
  //     timeout: 120 * 1000,
  //     stdout: 'pipe',
  //     stderr: 'pipe',
  //   },
  // ],
  
  /* Global timeout for all tests */
  timeout: 60 * 1000, // 1 minute per test
});
