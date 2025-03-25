# Activity Categorizer

A Python library for categorizing activities in ActivityWatch as productive, procrastinating, or unclear.

## Features

- Rule-based activity categorization
- URL and application name matching
- Case-insensitive pattern matching
- Configurable categorization rules
- Integration with ActivityWatch

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Install the watchers for your:
- Browser: [aw-watcher-web](https://github.com/ActivityWatch/aw-watcher-web) - The official browser extension, supports Chrome, Edge, and Firefox. If you're using a different browser, please let me know.
- IDE: [VSCode/Cursor](https://github.com/ActivityWatch/aw-watcher-vscode), many others available, see [this list](https://docs.activitywatch.net/en/latest/watchers.html#editor-watchers)

## Usage

Run the script:
```bash
python procrastination-monitor.py
```
