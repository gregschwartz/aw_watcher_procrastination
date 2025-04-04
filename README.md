# ActivityWatch Procrastination Monitor

Procrastination is a common problem, often becase you're overwhelmed with a task, or scared of it, or just can't even figure out where to start on it. 

And it's often hard to catch yourself procrastinating! This app pops up when you're procrastinating, and then you can chat with a productivity assistant to help you get unstuck.

## Features

- **Pop up when you're procrastinating** by monitoring the apps and URLs you're using
- **Get unstuck** by chatting with a productivity assistant, which coaches you to figure out what is in the way and how to break it down so it's easy to start
- **Completely private** your activity is only stored on your own computer, using the open source project [ActivityWatch](https://activitywatch.net)

## Easy Installation

1. Install ActivityWatch: https://activitywatch.net/

2. Install the watchers for your:
    - Browser: [aw-watcher-web](https://github.com/ActivityWatch/aw-watcher-web) - The official browser extension, supports Chrome, Edge, and Firefox. If you're using a different browser, please let me know.
    - IDE: [VSCode/Cursor](https://github.com/ActivityWatch/aw-watcher-vscode), many others available, see [this list](https://docs.activitywatch.net/en/latest/watchers.html#editor-watchers)

3. Clone this repository:
    ```bash
    git clone https://github.com/gregschwartz/aw-watcher-procrastination.git
    cd aw-watcher-procrastination
    ```

## Start the application

Start the application normally:
- On Unix/macOS
    ```bash
    ./start.sh
    ```

- On Windows
    ```bash
    start.bat
    ```

----

## If easy installation doesn't work, manually do it

1. Install ActivityWatch: https://activitywatch.net/

2. Install the watchers for your:
    - Browser: [aw-watcher-web](https://github.com/ActivityWatch/aw-watcher-web) - The official browser extension, supports Chrome, Edge, and Firefox. If you're using a different browser, please let me know.
    - IDE: [VSCode/Cursor](https://github.com/ActivityWatch/aw-watcher-vscode), many others available, see [this list](https://docs.activitywatch.net/en/latest/watchers.html#editor-watchers)

3. Clone this repository:
    ```bash
    git clone https://github.com/gregschwartz/aw_watcher_procrastination.git
    cd aw_watcher_procrastination
    ```

4. Create and activate a virtual environment:
    - On Unix/macOS
      ```bash
      python -m venv .venv
      source .venv/bin/activate
      ```
    - On Windows
      ```bash
      python -m venv .venv
      .venv\Scripts\activate
      ```

5. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

    Note: You may need to install additional system dependencies for QtWebEngine:
    - macOS: `brew install qt@6`
    - Ubuntu/Debian: `apt-get install qt6-webengine-dev`

6. Copy settings.json.example to settings.json
    ```bash
    cp settings.json.example settings.json
    ```

7. Start the application directly:
    ```bash
    python -m src.aw_watcher_procrastination.main
    ```
