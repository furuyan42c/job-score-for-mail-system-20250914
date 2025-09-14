# Special Guidelines and Patterns

## Super Claude Framework Integration

### Core Principles
- **Task-First Approach**: Understand → Plan → Execute → Validate
- **Evidence-Based**: All decisions backed by testing or documentation
- **Parallel Thinking**: Maximize efficiency through parallel operations
- **Context Awareness**: Maintain project understanding across sessions

### Command Workflow
1. **Start Feature**: `./scripts/create-new-feature.sh "description"`
2. **Specify**: `/specify [--think-hard] [--brainstorm]`
3. **Plan**: `/plan [--optimize-parallel] [--research-heavy]`
4. **Tasks**: `/tasks [--parallel-optimization] [--mcp-strategy]`
5. **Implement**: Use TodoWrite for task management
6. **Verify**: `/verify-and-pr <slug> "message" [--comprehensive]`

### MCP Server Usage Patterns
- **Sequential**: For deep analysis and complex reasoning
- **Context7**: For documentation and framework patterns
- **Serena**: For semantic code operations and memory
- **Magic**: For UI component generation
- **Playwright**: For browser testing
- **IDE**: For VS Code integration

### Parallel Execution Strategy
- Always identify parallelizable tasks during planning
- Use batch operations for file reads/edits
- Run independent tests concurrently
- Optimize tool calls for efficiency

## Spec-Kit Patterns

### Specification Structure
- **spec.md**: Functional requirements and user stories
- **plan.md**: Technical implementation approach
- **tasks.md**: Granular task breakdown with IDs

### Task ID Format
- Format: `TNNN` (e.g., T001, T002)
- Sequential numbering within feature
- Reference in commits: `[T001]`

## Git Workflow
- Feature branches: `NNN-feature-name`
- Never work directly on main/master
- Commit after each task completion
- Use conventional commit format

## Quality Standards
- Test coverage: minimum 80%
- All linting must pass before commit
- Documentation for public APIs required
- Type hints/types for all functions

## Session Management
- Always `/sc:load` at session start
- Create checkpoints every 30 minutes
- `/sc:save` before ending session
- Use memories for cross-session context

## Business Analysis
- Run `/sc:business-panel` for strategic features
- Document business value in specifications
- Consider trade-offs in implementation

## Important Notes
- Current branch: 001-think-hard-manual (manual validation focus)
- Morphllm MCP is deprecated in v2.3 (use Serena + MultiEdit)
- Always validate manual changes with `/validate-manual`
- Prioritize parallel operations for efficiency