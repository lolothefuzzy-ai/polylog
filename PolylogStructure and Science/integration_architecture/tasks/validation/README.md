# Validation Tasks — Test Suites & Benchmarks

## TASK-VAL-001: Performance FPS Harness

- **File:** `tests/performance/test_fps.js`
- **Dependencies:** `puppeteer`
- **Code Stub:**

  ```javascript
  const puppeteer = require('puppeteer')

  test('Maintains 30 FPS with 1000 polyforms', async () => {
    const browser = await puppeteer.launch({ headless: 'new', args: ['--enable-features=VaapiVideoDecoder'] })
    const page = await browser.newPage()

    await page.goto('http://localhost:3000')
    await page.waitForSelector('canvas')

    const fps = await page.evaluate(() => {
      return new Promise(resolve => {
        let frames = 0
        const start = performance.now()

        function measure() {
          frames += 1
          const elapsed = performance.now() - start
          if (elapsed >= 1000) {
            resolve(frames)
          } else {
            requestAnimationFrame(measure)
          }
        }

        requestAnimationFrame(measure)
      })
    })

    expect(fps).toBeGreaterThanOrEqual(30)
    await browser.close()
  }, 30000)
  ```

- **Validation:** test passes on CI headless run; scene maintains ≥30 FPS with instancing enabled
- **Resources:** Puppeteer evaluation docs <https://pptr.dev/>;
  WebGL-on-CI setup notes

## TASK-VAL-002: Memory Leak Detection

- **File:** `tests/performance/test_memory.js`
- **Dependencies:** `puppeteer`
- **Code Stub:**

  ```javascript
  const puppeteer = require('puppeteer')

  test('No memory leak after 100 add/remove cycles', async () => {
    const browser = await puppeteer.launch({ headless: 'new', args: ['--js-flags=--expose-gc'] })
    const page = await browser.newPage()

    await page.goto('http://localhost:3000')
    await page.waitForSelector('canvas')

    const initialHeap = (await page.metrics()).JSHeapUsedSize

    await page.evaluate(async () => {
      for (let i = 0; i < 100; i += 1) {
        await window.polyforms.add({ uuid: `stress-${i}` })
        await window.polyforms.remove(`stress-${i}`)
      }
    })

    await page.evaluate(() => window.gc && window.gc())

    const finalHeap = (await page.metrics()).JSHeapUsedSize
    expect(finalHeap - initialHeap).toBeLessThan(10 * 1024 * 1024)

    await browser.close()
  }, 30000)
  ```

- **Validation:** Heap growth <10 MB after stress cycle; requires Node launched with `--expose-gc`
- **Resources:** Chrome DevTools protocol metrics <https://chromedevtools.github.io/devtools-protocol/>
