| Task                                                | Command                                                                                |
| --------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Validate a skill (no argument: every skill)         | `python3 tools/skilllint.py <skill>`                                                   |
| Test the linter                                     | `python3 -m unittest tools/test_skilllint.py`                                          |
| Reinstall a skill (the post-commit hook does this)  | `npx -y skills add ~/.kevintraver/agents/skills -g -s <skill> -a claude-code codex -y` |
