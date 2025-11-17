# Browser Launch Coordinator

## Overview

The Browser Launch Coordinator manages browser launches for testing with intelligent rate limiting, test result analysis, and test-driven development workflow guidance.

## Key Features

- **Rate Limiting**: Minimum 1-minute cooldown between browser launches
- **Test Result Analysis**: Automatically analyzes test output for passes, failures, and missing functionality
- **Early Termination**: Automatically terminates browsers if missing functionality is detected
- **Workflow Guidance**: Provides next steps based on test results
- **Session Management**: Tracks browser sessions and prevents browser explosion

## Usage

### Check Status

```bash
python scripts/browser_coordinator.py --status
```

### Run Tests with Coordination

```bash
# Run with full workflow (recommended)
python scripts/coordinated_test_runner.py --workflow --type visual

# Run specific test files
python scripts/coordinated_test_runner.py --type integration --files tests/integration/test1.spec.js

# Check if browser can be launched
python scripts/browser_coordinator.py --can-launch
```

### Terminate a Session

```bash
python scripts/browser_coordinator.py --terminate session_1234567890
```

### Clean Up Old Sessions

```bash
python scripts/browser_coordinator.py --cleanup
```

## Workflow

### Test-Driven Development Flow

1. **Check Readiness**: Coordinator checks if browser can be launched
   - Verifies no active sessions
   - Checks cooldown period (1 minute minimum)

2. **Run Tests**: Launches browser and runs tests
   - Tracks session ID
   - Monitors test execution

3. **Analyze Results**: Automatically analyzes test output
   - Detects passes, failures, errors
   - Identifies missing functionality
   - Extracts missing feature names

4. **Provide Guidance**: Generates next steps based on results
   - **Pass**: Review coverage, add features
   - **Fail**: Fix backend code, re-run tests
   - **Missing Functionality**: Implement features, update API
   - **Error**: Check servers, review logs

5. **Early Termination**: If missing functionality detected
   - Browser is terminated immediately
   - Session marked as terminated
   - Guidance provided for implementation

6. **Cooldown**: Enforces minimum time between launches
   - Prevents browser explosion
   - Allows time to implement fixes
   - Ensures tests can be properly analyzed

## Integration

The coordinator integrates with existing test scripts:

- `scripts/run_tests_in_workspace.py` - Automatically uses coordinator when available
- `scripts/automated_test_pipeline.py` - Can be updated to use coordinator
- `scripts/start_tests_now.py` - Can be updated to use coordinator

## State Management

The coordinator maintains state in `.browser_coordinator_state.json`:
- Last launch time
- Active sessions
- Test history
- Next steps

This file is automatically created and updated. It's excluded from git via `.gitignore`.

## Best Practices

1. **Always use `--workflow` flag** for test-driven development
2. **Review next steps** after each test run
3. **Implement fixes** before running tests again
4. **Terminate sessions** if you need to stop testing early
5. **Check status** before running tests to avoid conflicts

## Example Session

```bash
# Check if ready
$ python scripts/browser_coordinator.py --can-launch
Can launch: True
Reason: Ready to launch

# Run tests with workflow
$ python scripts/coordinated_test_runner.py --workflow --type visual

[COORDINATOR] Browser session session_1234567890 launched
[TEST RUNNER] Running tests in session session_1234567890...
[TEST RUNNER] Command: npm run test:visual --project=chromium --headed

============================================================
Test Results Summary
============================================================
Session ID: session_1234567890
Result: missing_functionality
Missing Features: ['polyform_generator', 'api_endpoint']
Exit Code: 1

Next Steps:
  ⚠ Missing functionality detected:
    - polyform_generator
    - api_endpoint
  → Implement missing features in backend
  → Update API endpoints if needed
  → Re-run tests after implementation
============================================================

[TEST RUNNER] Missing functionality detected - session terminated
[TEST RUNNER] Implement missing features before running tests again

# Check status
$ python scripts/browser_coordinator.py --status
Can launch browser: False
Reason: Cooldown period active. Wait 45.2 more seconds.
```

## Troubleshooting

### "Cannot launch browser: Active browser session(s) still running"

Terminate existing sessions:
```bash
python scripts/browser_coordinator.py --status  # Find session IDs
python scripts/browser_coordinator.py --terminate <session_id>
```

### "Cooldown period active"

Wait for the cooldown period to expire, or check status to see remaining time.

### Import Errors

Ensure you're running from the project root:
```bash
cd /path/to/polylog6
python scripts/coordinated_test_runner.py --workflow
```

## Configuration

Edit `scripts/browser_coordinator.py` to adjust:
- `MIN_COOLDOWN_SECONDS`: Minimum time between launches (default: 60)
- `STATE_FILE`: Location of state file (default: `.browser_coordinator_state.json`)

