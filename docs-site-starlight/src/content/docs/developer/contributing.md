---
sidebar_position: 1
title: Contributing to AX POC
description: Git Flow 브랜치 전략, 커밋 컨벤션, 코드 스타일, PR 프로세스 등 코드 기여 가이드
tags: [개발자, 가이드, 기여, 컨벤션]
---

# 기여 가이드 (Contributing to AX POC)

> Git Flow 브랜치 전략, Conventional Commits, Python/TypeScript 코드 스타일, PR 프로세스를 정의한다.

## Git Workflow

### Branch Strategy (Git Flow)

We follow **Git Flow** with these branches:

```
main (production)
  ↓
develop (integration)
  ↓
feature/* (new features)
hotfix/* (urgent fixes)
release/* (release prep)
```

#### Branch Types

1. **main** - Production-ready code
   - Protected branch
   - Only merge from `develop` or `hotfix/*`
   - Tagged with version numbers (v1.0.0, v2.0.0)

2. **develop** - Integration branch
   - Latest development code
   - Merge destination for all `feature/*` branches
   - Always stable and deployable

3. **feature/** - New features or enhancements
   - Branch from: `develop`
   - Merge to: `develop`
   - Naming: `feature/enhancement-ocr-pipeline`, `feature/add-vl-model`

4. **hotfix/** - Urgent production fixes
   - Branch from: `main`
   - Merge to: `main` AND `develop`
   - Naming: `hotfix/fix-gdt-detection`, `hotfix/memory-leak`

5. **release/** - Release preparation
   - Branch from: `develop`
   - Merge to: `main` AND `develop`
   - Naming: `release/v2.0.0`

### Commit Message Convention

Follow **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code restructuring (no feature/bug change)
- `perf`: Performance improvement
- `test`: Add/update tests
- `chore`: Build process, dependencies, tooling
- `ci`: CI/CD configuration
- `revert`: Revert previous commit

#### Examples

```bash
# Feature
feat(enhancers): add VL model integration for GD&T detection

Implements GPT-4V and Claude 3 integration to improve GD&T recall
from 0% to 70-75%. Uses Strategy Pattern with Factory.

Closes #42

# Bug fix
fix(edocr): resolve GD&T box detection returning empty results

EDGNet preprocessor now correctly merges nearby candidate regions.
GD&T recall improved from 0% to 50%.

Fixes #38

# Refactor
refactor(enhancers): apply Strategy and Factory patterns

- Extract abstract base classes
- Implement StrategyFactory
- Add ConfigManager singleton
- Create exception hierarchy

Improves maintainability and testability.

# Documentation
docs(readme): update architecture diagram and setup instructions

# Chore
chore(deps): upgrade opencv-python to 4.8.1.78
```

### Workflow Steps

#### 1. Start a New Feature

```bash
# Update develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ... code ...

# Commit with conventional format
git add .
git commit -m "feat(scope): description"

# Push to remote
git push origin feature/your-feature-name

# Create Pull Request to develop
```

#### 2. Create a Release

```bash
# Branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v2.0.0

# Update version numbers
# ... update package.json, __init__.py, etc. ...

# Commit
git commit -m "chore(release): bump version to 2.0.0"

# Merge to main
git checkout main
git merge --no-ff release/v2.0.0
git tag -a v2.0.0 -m "Release version 2.0.0"
git push origin main --tags

# Merge back to develop
git checkout develop
git merge --no-ff release/v2.0.0
git push origin develop

# Delete release branch
git branch -d release/v2.0.0
```

#### 3. Hotfix

```bash
# Branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug

# Fix the bug
# ... code ...

# Commit
git commit -m "fix(api): resolve critical bug"

# Merge to main
git checkout main
git merge --no-ff hotfix/critical-bug
git tag -a v2.0.1 -m "Hotfix: critical bug"
git push origin main --tags

# Merge to develop
git checkout develop
git merge --no-ff hotfix/critical-bug
git push origin develop

# Delete hotfix branch
git branch -d hotfix/critical-bug
```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Docstrings for all public functions/classes (Google style)
- Max line length: 100 characters

```python
def enhance_gdt(
    self,
    image_path: Path,
    img: np.ndarray,
    original_gdt: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Enhance GD&T detection using specified strategy.

    Args:
        image_path: Path to image file
        img: Image array
        original_gdt: Original GD&T results from eDOCr

    Returns:
        Enhanced GD&T list with improved recall

    Raises:
        EnhancementError: If enhancement fails
    """
    pass
```

### TypeScript/React

- Follow Airbnb style guide
- Use ESLint and Prettier
- Functional components with hooks
- Props with TypeScript interfaces

```typescript
interface EnhancementStrategySelectorProps {
  value: EnhancementStrategy;
  onChange: (strategy: EnhancementStrategy) => void;
  disabled?: boolean;
}

export default function EnhancementStrategySelector({
  value,
  onChange,
  disabled = false,
}: EnhancementStrategySelectorProps) {
  // ...
}
```

## Testing

### Running Tests

```bash
# Python tests
cd models/edocr2-v2-api
pytest tests/

# TypeScript tests
cd web-ui
npm test

# Integration tests
./run_integration_tests.sh
```

### Writing Tests

- Unit tests for all new functions
- Integration tests for API endpoints
- E2E tests for critical workflows

## Pull Request Process

1. **Create PR** with clear title and description
2. **Link issues** using "Closes #123" or "Fixes #456"
3. **Pass CI checks** (linting, tests, build)
4. **Request review** from maintainers
5. **Address feedback** and update PR
6. **Squash commits** if requested
7. **Merge** after approval

## Directory Structure

```
ax/poc/
├── models/edocr2-v2-api/ # eDOCr v2 API
│   ├── enhancers/       # Enhancement modules
│   │   ├── base.py      # Abstract interfaces
│   │   ├── strategies.py # Strategy implementations
│   │   ├── factory.py   # Strategy factory
│   │   ├── config.py    # Configuration
│   │   └── utils.py     # Utilities
│   ├── api_server_edocr_v1.py
│   └── requirements_v1.txt
├── edgnet-api/          # EDGNet API
├── skinmodel-api/       # Skin Model API
├── gateway-api/         # Gateway orchestrator
├── web-ui/              # React frontend
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── lib/         # API clients
│   │   └── pages/       # Page components
│   └── package.json
└── docs/                # Documentation
```

## Questions?

- GitHub Issues: Technical questions, bug reports
- Pull Requests: Code review, feedback
- Documentation: Check README.md and docs/

## 관련 문서

- [Git Workflow](/docs/developer/git-workflow) — 브랜치 전략 및 커밋 워크플로우 상세
- [LLM Usability](/docs/developer/llm-usability) — LLM 친화적 코드 작성 가이드
- [CI 파이프라인](/docs/devops/ci-pipeline) — 자동화된 린트, 테스트, 빌드
