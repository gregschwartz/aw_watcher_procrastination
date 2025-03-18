<!--
SPDX-FileCopyrightText: 2021 Bernardo Chrispim Baron <bc.bernardo@hotmail.com>

SPDX-License-Identifier: MIT
-->

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

3. For development, install additional tools:
```bash
pip install -r dev-requirements.txt
```

## Usage

```python
from activity_categorizer import ActivityCategorizer, ActivityCategory

# Create a categorizer
categorizer = ActivityCategorizer()

# Add rules
categorizer.add_rule("facebook.com", ActivityCategory.PROCRASTINATING, is_url=True)
categorizer.add_rule("github.com", ActivityCategory.PRODUCTIVE, is_url=True)
categorizer.add_rule("Visual Studio Code", ActivityCategory.PRODUCTIVE)

# Check if an activity is procrastinating
is_proc = categorizer.is_procrastinating("Chrome", "https://www.facebook.com")  # True
is_proc = categorizer.is_procrastinating("Visual Studio Code")  # False
```

## Development

### Running Tests

Run tests with pytest:
```bash
pytest test_activity_categorizer.py -v
```

Run tests with coverage:
```bash
pytest --cov=activity_categorizer --cov-report=term-missing
```

### Code Quality

Format code:
```bash
black .
isort .
```

Run type checking:
```bash
mypy activity_categorizer.py
```

Run linting:
```bash
flake8 .
```

## Configuration

The project uses several configuration files:

- `pyproject.toml` - Configuration for black, isort, pytest, and mypy
- `requirements.txt` - Core project dependencies
- `dev-requirements.txt` - Development dependencies

## License

MIT License
