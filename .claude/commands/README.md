# Custom Claude Code Commands

This directory contains workflow templates for common tasks.

## Available Commands

### `/test-api`
Test individual API endpoints with various scenarios. Provides curl commands for:
- YOLO API
- eDOCr2 v2 API
- PaddleOCR API
- Gateway Speed Mode
- Gateway Hybrid Mode

### `/debug-issue`
Debug common issues following systematic workflow:
- Check logs
- Common issue patterns ("바운딩박스 값이 안나와요", API 500, Container unhealthy)
- Document in KNOWN_ISSUES.md

### `/add-feature`
Add a new feature to an API following modular structure:
1. Create service module
2. Export from __init__.py
3. Add response model
4. Use in api_server.py
5. Test and document

### `/rebuild-service`
Rebuild and restart a Docker service safely:
- Single service rebuild
- All services rebuild
- Health verification
- Docker cache cleanup

### `/track-issue`
Track user-reported issue in KNOWN_ISSUES.md:
- Template for "안된다" (It doesn't work)
- Template for "잘된다" (It works)
- Investigation workflow
- Resolution workflow

## Usage

Simply type the command name in the chat:
```
/test-api
/debug-issue
/add-feature gateway-api
/rebuild-service yolo-api
/track-issue
```

Claude Code will expand the prompt and guide you through the workflow.

## Best Practices

1. Use commands for repetitive tasks
2. Follow the templates for consistency
3. Update KNOWN_ISSUES.md when tracking issues
4. Update ROADMAP.md when completing tasks
5. Document lessons learned
