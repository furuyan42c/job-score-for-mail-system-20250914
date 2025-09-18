---
# Create a session checkpoint
---

MILESTONE="$ARGUMENTS"
if [ -z "$MILESTONE" ]; then
  MILESTONE="Checkpoint at $(date '+%H:%M')"
fi

echo "🏁 Creating checkpoint: $MILESTONE"
echo "  - Files modified: $(git status --porcelain | wc -l)"
echo "  - Time elapsed: Check session logs"
echo "✅ Checkpoint created: $MILESTONE"