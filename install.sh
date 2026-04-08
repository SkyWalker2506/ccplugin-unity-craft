#!/usr/bin/env bash
set -euo pipefail

# ccplugin-unity-craft installer
# Copies skill files to claude-config global skills directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${HOME}/Projects/claude-config/global/skills"

echo "Installing unity-craft plugin..."

# Create skill directory
mkdir -p "$SKILLS_DIR/unity-craft"

# Copy skill file
cp "$SCRIPT_DIR/skills/unity-craft/SKILL.md" "$SKILLS_DIR/unity-craft/SKILL.md"

echo "Done. unity-craft skill installed to $SKILLS_DIR/unity-craft/"
echo ""
echo "Requirements:"
echo "  1. Install com.skywalker.craft in your Unity project"
echo "  2. Ensure com.unity.ai.assistant MCP bridge is active"
echo "  3. Configure Unity MCP server in Claude Code settings"
