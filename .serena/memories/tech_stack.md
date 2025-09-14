# Tech Stack and Dependencies

## JavaScript/TypeScript Stack
- **Runtime**: Node.js 18+
- **Framework**: Next.js (configured)
- **Type System**: TypeScript with tsconfig.json
- **Package Manager**: npm
- **Module Type**: ESM (ES Modules)

## Python Stack
- **Version**: Python 3.9+ (pyproject.toml configured)
- **Build System**: setuptools with pyproject.toml
- **Virtual Environment**: .venv directory present

## Development Tools
- **Linting (JS/TS)**: ESLint with custom rules
- **Formatting (JS/TS)**: Prettier with configuration
- **Linting (Python)**: Flake8 with custom configuration
- **Formatting (Python)**: Black (line-length: 100)
- **Type Checking (Python)**: mypy with strict settings
- **Import Sorting (Python)**: isort with Black profile
- **Testing (Python)**: pytest with coverage requirements (80% minimum)

## MCP Servers Available
- **Sequential**: Deep analysis and structured reasoning
- **Context7**: Documentation lookup and framework patterns
- **Serena**: Semantic code understanding and project memory
- **Magic**: UI component generation from 21st.dev
- **Playwright**: Browser automation and E2E testing
- **IDE**: VS Code integration

## Configuration Files
- `.eslintrc.json`: ESLint configuration
- `.prettierrc.json`: Prettier formatting rules
- `.flake8`: Python linting configuration
- `pyproject.toml`: Python project configuration with all tools
- `tsconfig.json`: TypeScript compiler options
- `mcp-config.json`: MCP server configuration
- `.editorconfig`: Editor configuration for consistency