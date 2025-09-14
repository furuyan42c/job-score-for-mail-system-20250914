# Project Structure

## Directory Organization

```
/Users/naoki/000_PROJECT/作業用/
├── .000.MANUAL/                 # Super Claude documentation
│   └── super_claude_integrated_manual_v2.3.md
├── .claude/                      # Claude Code configuration
│   └── commands/                 # Spec-Kit command definitions
│       ├── specify.md
│       ├── plan.md
│       ├── tasks.md
│       └── verify-and-pr.md
├── .devcontainer/                # VS Code dev container config
├── .serena/                      # Serena MCP memory storage
├── .venv/                        # Python virtual environment
├── memory/                       # Session persistence storage
├── scripts/                      # Utility scripts
│   └── create-new-feature.sh    # Feature branch creation
├── specs/                        # Project specifications
│   └── <feature-branches>/      # Feature-specific specs
├── templates/                    # Project templates
│   ├── spec-template.md
│   ├── plan-template.md
│   ├── tasks-template.md
│   └── agent-file-template.md
├── AGENT.md                      # Claude Code agent description
├── CLAUDE.md                     # Main operational guide
├── README.md                     # Project overview
└── [Config files]                # Various configuration files
```

## Key Directories

### specs/
- Contains all project specifications
- Organized by feature branch name (e.g., `001-auth-system/`)
- Each feature has: spec.md, plan.md, tasks.md

### templates/
- Reusable templates for specifications
- Used by create-new-feature.sh script
- Maintain consistency across features

### .claude/commands/
- Spec-Kit command definitions
- Define behavior for /specify, /plan, /tasks, /verify-and-pr
- Custom Claude Code commands

### memory/ and .serena/
- Cross-session persistence
- Project context and state
- Memory files for continuity

## File Naming Patterns
- Feature directories: `NNN-feature-name/` (e.g., `001-auth-system/`)
- Specs: Always `spec.md`, `plan.md`, `tasks.md`
- Scripts: kebab-case with `.sh` extension
- Config files: Standard names (.eslintrc.json, pyproject.toml, etc.)

## Working Areas
- **Development**: Main project root
- **Documentation**: .000.MANUAL/ and project root markdown files
- **Specifications**: specs/ directory
- **Automation**: scripts/ directory