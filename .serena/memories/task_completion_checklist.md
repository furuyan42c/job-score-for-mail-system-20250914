# Task Completion Checklist

## MANDATORY Steps After Completing Any Task

### 1. Code Quality Checks
```bash
# For JavaScript/TypeScript changes
npm run lint        # Check for linting errors
npm run format      # Auto-format code

# For Python changes
black .             # Format Python code
isort .             # Sort imports
flake8              # Check linting
mypy .              # Type checking
```

### 2. Test Execution
```bash
# Run tests if they exist
pytest              # Python tests
npm test            # JavaScript tests (if configured)
```

### 3. Git Operations
```bash
# Check what changed
git status
git diff

# Stage and commit with conventional format
git add .
git commit -m "type(scope): description"
```

### 4. Documentation Updates
- Update README if functionality changed
- Update inline comments if logic changed
- Update API documentation if endpoints changed

### 5. Validation with Super Claude
```bash
# In Claude Code, run:
/verify-and-pr <slug> "description" --comprehensive
```

## Quality Gates That Must Pass
- ✅ No linting errors
- ✅ Code properly formatted
- ✅ Type checking passes (if applicable)
- ✅ Tests pass (if they exist)
- ✅ No console.log left (except intentional)
- ✅ No commented-out code
- ✅ No TODO comments for completed work

## Special Considerations
- If working on branch 001-think-hard-manual, ensure manual is validated
- If MCP servers were used, document which ones and why
- If parallel operations were possible but not used, note for optimization

## Rollback Plan
If any quality check fails:
1. Do NOT commit broken code
2. Fix issues first
3. Re-run all checks
4. Only commit when all checks pass