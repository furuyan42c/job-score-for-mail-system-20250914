---
# Load project context and initialize Super Claude session
---

echo "🚀 Loading Super Claude session..."
echo "📊 Project: $(basename $(pwd))"
echo "🌿 Branch: $(git branch --show-current)"
echo "✅ Session initialized"

# Context markers for Claude
echo "[SUPER_CLAUDE_SESSION_ACTIVE]"
echo "Available MCP servers: Sequential, Context7, Serena, Magic, Playwright"
echo "Framework version: 4.1.1"