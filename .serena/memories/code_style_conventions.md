# Code Style and Conventions

## JavaScript/TypeScript Conventions

### Naming
- **Files**: kebab-case (e.g., `user-auth.ts`, `api-client.js`)
- **Variables/Functions**: camelCase (e.g., `getUserData`, `isValid`)
- **Classes/Types**: PascalCase (e.g., `UserModel`, `ApiResponse`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `API_URL`)

### ESLint Rules
- No unused variables (except those prefixed with `_`)
- Prefer const over let, no var
- Use arrow functions where appropriate
- Use template literals over string concatenation
- Object shorthand required
- No duplicate imports

### Code Style
- ES2022 features allowed
- ES Modules (import/export)
- Async/await preferred over callbacks
- 2 spaces indentation (enforced by Prettier)

## Python Conventions

### Naming
- **Files**: snake_case (e.g., `user_auth.py`, `api_client.py`)
- **Variables/Functions**: snake_case (e.g., `get_user_data`, `is_valid`)
- **Classes**: PascalCase (e.g., `UserModel`, `ApiClient`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `API_URL`)

### Black Formatting
- Line length: 100 characters
- Target Python 3.9+
- Automatic formatting, no manual style decisions

### Type Hints
- **Required**: All function signatures must have type hints
- **mypy strict mode**: Enabled for type checking
- Example:
```python
def process_data(input_data: List[str], validate: bool = True) -> Dict[str, Any]:
    pass
```

### Docstrings
- Use triple quotes for docstrings
- Follow Google style or NumPy style consistently
- Include parameter descriptions and return values

### Import Order (enforced by isort)
1. Standard library imports
2. Third-party imports
3. Local application imports
- Alphabetical within each group

## Git Commit Conventions
- Use conventional commits format:
  - `feat:` New feature
  - `fix:` Bug fix
  - `docs:` Documentation only
  - `style:` Code style (formatting, missing semicolons, etc.)
  - `refactor:` Code refactoring
  - `test:` Adding or updating tests
  - `chore:` Build process or auxiliary tool changes
- Keep commits atomic and focused
- Write clear, descriptive commit messages

## Documentation Standards
- Code should be self-documenting with clear names
- Add comments only for complex logic or business rules
- Keep README files updated
- Document API endpoints and data structures
- Use markdown for all documentation

## Testing Conventions
- Test files: `test_*.py` or `*.test.js`
- One test file per module/component
- Use descriptive test names
- Aim for 80% code coverage minimum
- Mark slow tests with appropriate markers