# Git Workflow Guide

## Quick Reference

### Current Project Status

```
Branch: feature/enhancement-ocr-pipeline
Base: develop (to be created)
Status: Ready for initial commit
```

### Setup Commands

```bash
# Initialize Git (if not already)
cd /home/uproot/ax/poc
git init

# Create main and develop branches
git checkout -b main
git add .
git commit -m "chore(init): initial project structure"

git checkout -b develop
git push -u origin main
git push -u origin develop

# Create feature branch
git checkout -b feature/enhancement-ocr-pipeline
```

## Committing Enhanced OCR Implementation

### Step 1: Stage Changes by Module

```bash
# Config and base classes
git add edocr2-api/enhancers/config.py
git add edocr2-api/enhancers/exceptions.py
git add edocr2-api/enhancers/base.py
git commit -m "feat(enhancers): add config management and base classes

- Implement ConfigManager with Singleton pattern
- Define exception hierarchy for error handling
- Create abstract base classes (Strategy, Detector, Preprocessor)
- Follow SOLID principles for extensibility

Ref: ENHANCEMENT_IMPLEMENTATION_SUMMARY.md"

# Strategy implementations
git add edocr2-api/enhancers/strategies.py
git add edocr2-api/enhancers/factory.py
git add edocr2-api/enhancers/utils.py
git commit -m "feat(enhancers): implement enhancement strategies with Factory pattern

- BasicStrategy: baseline eDOCr
- EDGNetStrategy: GraphSAGE preprocessing (50-60% GD&T recall)
- VLStrategy: GPT-4V/Claude 3 integration (70-75% GD&T recall)
- HybridStrategy: EDGNet + VL ensemble (80-85% GD&T recall)
- StrategyFactory: centralized strategy creation
- GDTResultMerger: deduplication and merging

Improves GD&T detection from 0% to 50-85% depending on strategy."

# Preprocessor and detector
git add edocr2-api/enhancers/edgnet_preprocessor.py
git add edocr2-api/enhancers/vl_detector.py
git add edocr2-api/enhancers/enhanced_pipeline.py
git commit -m "feat(enhancers): add EDGNet preprocessor and VL detector

- EDGNetPreprocessor: connects to EDGNet API for segmentation
- VLDetector: integrates GPT-4V and Claude 3 for GD&T detection
- EnhancedOCRPipeline: orchestrates strategies (legacy support)

Follows Adapter pattern for external service integration."

# Module exports
git add edocr2-api/enhancers/__init__.py
git commit -m "feat(enhancers): export public API with version 2.0.0

- Expose StrategyFactory as recommended interface
- Export base classes for extension
- Maintain backward compatibility with legacy API
- Document architecture and design patterns"

# API endpoint
git add edocr2-api/api_server_edocr_v1.py
git commit -m "feat(api): add /api/v1/ocr/enhanced endpoint

- New endpoint supports 4 enhancement strategies
- Backward compatible with existing /api/v1/ocr
- Returns enhancement metadata (stats, strategy info)
- Processing time: 45-80s depending on strategy

Resolves #38 (GD&T detection 0% issue)"

# Dependencies
git add edocr2-api/requirements_v1.txt
git commit -m "chore(deps): add requests for EDGNet integration

Add optional dependencies for VL models:
- openai>=1.0.0 (GPT-4V)
- anthropic>=0.34.0 (Claude 3)"

# Web UI components
git add web-ui/src/components/test/EnhancementStrategySelector.tsx
git add web-ui/src/lib/api.ts
git commit -m "feat(ui): add enhancement strategy selector component

- Visual strategy selection with performance metrics
- Support for 4 strategies (Basic, EDGNet, VL, Hybrid)
- VL provider selection (OpenAI/Anthropic)
- Add edocr2Api.ocrEnhanced() function

Provides user-friendly interface for choosing enhancement level."

# Documentation
git add ENHANCEMENT_IMPLEMENTATION_SUMMARY.md
git add PRODUCTION_READINESS_ANALYSIS.md
git commit -m "docs: add enhancement implementation and analysis docs

- ENHANCEMENT_IMPLEMENTATION_SUMMARY.md: implementation guide
- PRODUCTION_READINESS_ANALYSIS.md: performance analysis

Documents expected improvement: 43.5% → 70-88% Production Ready"

# Git configuration
git add .gitignore .gitattributes
git commit -m "chore(git): add gitignore and gitattributes

- Ignore Python cache, node_modules, model files
- Configure LFS for large model files
- Set line ending normalization"

# Contributing guide
git add CONTRIBUTING.md GIT_WORKFLOW.md
git commit -m "docs: add contributing guide and git workflow

- Define Git Flow branch strategy
- Conventional Commits specification
- Code style guidelines
- PR process documentation"
```

### Step 2: Push Feature Branch

```bash
# Push all commits
git push -u origin feature/enhancement-ocr-pipeline

# Create Pull Request on GitHub
# Title: "feat: Enhanced OCR with EDGNet and VL model integration"
# Description: Reference ENHANCEMENT_IMPLEMENTATION_SUMMARY.md
```

### Step 3: Merge to Develop

```bash
# After PR approval
git checkout develop
git merge --no-ff feature/enhancement-ocr-pipeline
git push origin develop

# Delete feature branch
git branch -d feature/enhancement-ocr-pipeline
git push origin --delete feature/enhancement-ocr-pipeline
```

## Daily Workflow

### Morning: Sync

```bash
git checkout develop
git pull origin develop
```

### During Development

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes, commit frequently
git add .
git commit -m "feat(scope): description"

# Push to backup
git push origin feature/my-feature
```

### End of Day: Cleanup

```bash
# Interactive rebase to squash commits
git rebase -i develop

# Force push (only on your feature branch!)
git push origin feature/my-feature --force-with-lease
```

## Tag Versions

```bash
# Semantic versioning: MAJOR.MINOR.PATCH
git tag -a v2.0.0 -m "Release: Enhanced OCR with EDGNet and VL"
git push origin v2.0.0

# List tags
git tag -l
```

## Useful Aliases

Add to `~/.gitconfig`:

```ini
[alias]
    st = status -sb
    co = checkout
    br = branch
    ci = commit
    lg = log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit
    unstage = reset HEAD --
    last = log -1 HEAD
    visual = log --graph --all --oneline --decorate
```

Usage:

```bash
git st          # Short status
git lg          # Pretty log
git visual      # Branch visualization
```

## Emergency Procedures

### Undo Last Commit (Not Pushed)

```bash
git reset --soft HEAD~1  # Keep changes staged
# or
git reset --hard HEAD~1  # Discard changes
```

### Undo Pushed Commit

```bash
git revert HEAD
git push origin develop
```

### Recover Deleted Branch

```bash
git reflog
git checkout -b recovered-branch <commit-hash>
```

## Best Practices

1. **Commit Often**: Small, focused commits are easier to review
2. **Write Good Messages**: Follow Conventional Commits
3. **Pull Before Push**: Always sync with remote before pushing
4. **Review Before Commit**: Use `git diff` to check changes
5. **Test Before Push**: Run tests locally first
6. **Never Force Push** to `main` or `develop`
7. **Use Branches**: One feature = one branch
8. **Keep History Clean**: Rebase feature branches before merging

## CI/CD Integration

When pushing, GitHub Actions will:

1. ✅ Lint code (black, eslint)
2. ✅ Run tests (pytest, jest)
3. ✅ Build Docker images
4. ✅ Security scan
5. ✅ Deploy to staging (on develop)
6. ✅ Deploy to production (on main)

---

**Current Branch**: `feature/enhancement-ocr-pipeline`
**Next Action**: Initial commit and push
**Target**: Merge to `develop` after review
