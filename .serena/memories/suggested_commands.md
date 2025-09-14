# Suggested Commands for Development

## Project Initialization
```bash
# Install JavaScript dependencies
npm install

# Set up Python virtual environment (if needed)
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
pip install -e ".[dev]"  # Install Python dev dependencies
```

## Linting and Formatting Commands

### JavaScript/TypeScript
```bash
# Linting
npm run lint

# Formatting
npm run format
```

### Python
```bash
# Formatting with Black
black .

# Linting with Flake8
flake8

# Type checking with mypy
mypy .

# Import sorting with isort
isort .

# Run all Python checks
black . && isort . && flake8 && mypy .
```

## Testing Commands

### Python
```bash
# Run tests with coverage
pytest

# Run specific test file
pytest tests/test_file.py

# Run tests with verbose output
pytest -v

# Run tests excluding slow tests
pytest -m "not slow"
```

## Feature Development Workflow
```bash
# Create new feature branch and directory
./scripts/create-new-feature.sh "feature description"

# Super Claude + Spec-Kit commands (in Claude Code)
/specify           # Generate specification
/plan             # Create implementation plan
/tasks            # Break down into tasks
/verify-and-pr    # Validate and create PR

# Session management (in Claude Code)
/sc:load          # Load project context
/sc:save          # Save session state
/sc:checkpoint    # Create checkpoint
/sc:business-panel # Analyze business value
```

## Git Commands
```bash
# Check status
git status

# View current branch
git branch

# Stage changes
git add .

# Commit with message
git commit -m "feat: description"

# Push to remote
git push -u origin branch-name

# Create PR using GitHub CLI (if installed)
gh pr create --title "title" --body "description"
```

## Darwin/macOS Specific Utils
```bash
# List files with details
ls -la

# Find files
find . -name "*.py"

# Search in files (use ripgrep if available)
rg "pattern"  # Preferred
grep -r "pattern" .  # Alternative

# Check disk usage
du -sh *

# Monitor processes
top
ps aux | grep process_name

# Open in default application
open file.txt
open .  # Open current directory in Finder
```

## Development Server Commands
```bash
# Next.js development server (if applicable)
npm run dev

# FastAPI development server (if applicable)  
uvicorn main:app --reload

# Python script execution
python script.py
```

## IMPORTANT: After Task Completion
1. **Always run linting**: `npm run lint` for JS/TS, `flake8` for Python
2. **Format code**: `npm run format` for JS/TS, `black .` for Python  
3. **Run tests if available**: `pytest` for Python
4. **Check git status**: `git status`
5. **Create meaningful commits**: Use conventional commit format