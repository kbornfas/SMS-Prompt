# SMS-Prompt
An SMS Prompt tool

## Development

### Git Hooks

This repository includes a pre-commit hook to check for uncommitted changes. To enable it:

```bash
git config core.hooksPath .githooks
```

To bypass the uncommitted changes check (when needed):
```bash
# Using environment variable
ALLOW_UNCOMMITTED=1 git commit -m "your message"

# Or using --no-verify flag
git commit --no-verify -m "your message"
```

You can also run the check manually:
```bash
./check-uncommitted.sh
```
