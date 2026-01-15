---
name: agent-browser
description: Browser automation CLI optimized for AI agents. Use `npx agent-browser` for all commands. Best for testing websites, verifying UI changes, checking console errors, taking screenshots, and automating form submissions.
---

# agent-browser

Browser automation CLI optimized for AI agents. Use `npx agent-browser` for all commands.

## When to Use

- Testing websites and web applications
- Verifying UI changes after code modifications
- Checking for console errors and page issues
- Taking screenshots for documentation or debugging
- Automating form submissions and user flows

## Core Workflow

**Always follow this pattern: snapshot → identify refs → act → snapshot again**

```bash
npx agent-browser open http://localhost:4321    # Navigate
npx agent-browser snapshot -i                    # Get interactive elements with refs
npx agent-browser click @e2                      # Act using ref from snapshot
npx agent-browser snapshot -i                    # Get updated state
```

Refs (e.g., `@e1`, `@e2`) are stable element identifiers from snapshots. Always use refs over CSS selectors when possible.

**Important:** Always use `snapshot -i` (interactive elements only) by default. This dramatically reduces output size by filtering to just buttons, links, inputs, and other actionable elements - which is usually all you need for browser automation. Only use full `snapshot` when you need to verify text content or page structure.

## Essential Commands

### Navigation
```bash
npx agent-browser open <url>        # Navigate to URL
npx agent-browser back              # Go back
npx agent-browser reload            # Reload page
npx agent-browser close             # Close browser
```

### Page Analysis
```bash
npx agent-browser snapshot -i       # Interactive elements only (preferred default)
npx agent-browser snapshot          # Full accessibility tree (when you need all content)
npx agent-browser snapshot -i -c    # Interactive + compact (minimal output)
npx agent-browser errors            # Check for JS errors
npx agent-browser console           # View console logs
```

### Interaction
```bash
npx agent-browser click @e1         # Click element
npx agent-browser fill @e2 "text"   # Clear field and type
npx agent-browser type @e2 "text"   # Type without clearing
npx agent-browser press Enter       # Press key
npx agent-browser hover @e3         # Hover element
npx agent-browser scroll down 500   # Scroll page
```

### Capture
```bash
npx agent-browser screenshot                    # Screenshot viewport
npx agent-browser screenshot --full             # Full page screenshot
npx agent-browser screenshot /path/to/file.png  # Save to specific path
npx agent-browser pdf /path/to/file.pdf         # Save as PDF
```

### Get Information
```bash
npx agent-browser get text @e1      # Get element text
npx agent-browser get url           # Get current URL
npx agent-browser get title         # Get page title
npx agent-browser get value @e2     # Get input value
```

## Common Testing Workflows

### Test a Local Dev Server
```bash
# Start dev server first (in background), then:
npx agent-browser open http://localhost:4321
npx agent-browser snapshot -i       # Get interactive elements
npx agent-browser errors            # Check for JS errors
npx agent-browser screenshot /tmp/homepage.png
```

### Test Navigation Flow
```bash
npx agent-browser open http://localhost:4321
npx agent-browser snapshot -i       # Find navigation links
npx agent-browser click @e5         # Click a nav link
npx agent-browser snapshot -i       # Verify new page loaded
```

### Test Dark Mode
```bash
npx agent-browser snapshot -i       # Find theme toggle
npx agent-browser click @e1         # Toggle theme
npx agent-browser screenshot /tmp/dark-mode.png
```

### Test Form Submission
```bash
npx agent-browser snapshot -i       # Get interactive elements
npx agent-browser fill @e3 "test@example.com"
npx agent-browser fill @e4 "message"
npx agent-browser click @e5         # Submit button
npx agent-browser snapshot -i       # Check result
```

## Snapshot Output Format

```
- document:
  - button "Toggle theme" [ref=e1]
  - main:
    - heading "Title" [ref=e2] [level=1]
    - link "About" [ref=e3]:
      - /url: /about
    - textbox "Email" [ref=e4]
```

- Elements have `[ref=eN]` for targeting
- Links show `/url:` with their href
- Headings show `[level=N]`
- Form elements show their type (textbox, checkbox, etc.)

## Snapshot Options

| Flag | Purpose |
|------|---------|
| `-i` | **Interactive elements only (recommended default)** - dramatically reduces context |
| `-c` | Compact (remove empty structural elements) |
| `-d 3` | Limit tree depth |
| `-s "#main"` | Scope to CSS selector |

Combine flags for minimal output: `npx agent-browser snapshot -i -c`

## Alternative Selectors

When refs aren't available, use:
```bash
npx agent-browser click "#submit"           # CSS selector
npx agent-browser click "text=Sign In"      # Text content
npx agent-browser find role button click --name "Submit"  # ARIA role
```

## Sessions (Multiple Browsers)

Run isolated browser instances:
```bash
npx agent-browser --session test1 open site-a.com
npx agent-browser --session test2 open site-b.com
```

## Tips for AI Agents

- **Always snapshot first**: Before clicking or typing, get a fresh snapshot to ensure valid refs
- **Use `-i` flag by default**: `snapshot -i` filters for interactive elements, dramatically reducing noise
- **Check output**: The CLI returns JSON or text; read it to confirm actions succeeded
- **Refs are ephemeral**: After any page change (navigation, click, form submit), take a new snapshot - old refs may be invalid

## Troubleshooting

**Browser not installed:**
```bash
npx agent-browser install
```

**Element not found:** Run `snapshot` again - refs change when page updates.

**Page still loading:** Add wait:
```bash
npx agent-browser wait 2000                 # Wait 2 seconds
npx agent-browser wait --load networkidle   # Wait for network idle
npx agent-browser wait --text "Success"     # Wait for specific text to appear
```
