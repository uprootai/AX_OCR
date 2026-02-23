# Docs Site Guide

## Overview

AX POC 문서 사이트 (Docusaurus 3.x) 관리 가이드.

## Location

```
docs-site/
├── docusaurus.config.ts      # Site configuration
├── sidebars.ts               # Sidebar structure (10 sections)
├── src/
│   ├── components/           # ServiceTable, StatusBadge, MetricCard
│   ├── data/                 # services.json, nodes.json
│   ├── css/custom.css        # Styles (badges, cards, metrics)
│   └── pages/index.tsx       # Landing page
├── docs/                     # 10 sections, 48 pages
│   ├── system-overview/      # (4 pages) Architecture, services, tech stack
│   ├── analysis-pipeline/    # (6 pages) VLM, YOLO, OCR, tolerance
│   ├── blueprintflow/        # (5 pages) Nodes, DAG, templates
│   ├── agent-verification/   # (4 pages) 3-level, API, dashboard
│   ├── bom-generation/       # (5 pages) Classes, pricing, export
│   ├── pid-analysis/         # (5 pages) Symbol, line, connectivity
│   ├── batch-delivery/       # (4 pages) Batch, project, export
│   ├── quality-assurance/    # (5 pages) GT, active learning, feedback
│   ├── frontend/             # (5 pages) Routing, state, components
│   └── devops/               # (5 pages) Docker, CI, CD, GPU
└── scripts/
    └── sync-data.ts          # Code → JSON sync script
```

## Commands

```bash
cd docs-site
npm run start     # Dev server (http://localhost:3000)
npm run build     # Production build
npm run serve     # Serve built site
```

## Adding New Documentation

### New Page in Existing Section

1. Create `.md` or `.mdx` file in the section folder
2. Add frontmatter: `sidebar_position`, `title`, `description`
3. Add entry to `sidebars.ts`
4. Run `npm run build` to verify

### New Section

1. Create folder in `docs/`
2. Create `index.md` (or `index.mdx`)
3. Add category to `sidebars.ts`
4. Update landing page sections in `src/pages/index.tsx`
5. Update footer links in `docusaurus.config.ts`

## MDX Gotchas

- **Curly braces**: `{variable}` in text is interpreted as JSX. Wrap in backticks.
- **Imports**: Use `import X from '@site/src/components/X'`
- **Mermaid**: Enabled via `@docusaurus/theme-mermaid`, use fenced code blocks

## Sync Triggers

| Code Change | Docs Update |
|-------------|-------------|
| New API service | system-overview/service-catalog + devops |
| New node type | blueprintflow/node-catalog |
| Pipeline change | analysis-pipeline diagrams |
| New verification level | agent-verification |
| Docker service change | devops/docker-compose |
| Frontend route | frontend/routing |
