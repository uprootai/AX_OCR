"""
eDOCr v1 Documentation Router
문서 관련 API 엔드포인트
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import markdown

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Documentation"])

# Documentation mapping
DOCS_MAP = {
    "user-guide": "USER_GUIDE.md",
    "quick-reference": "QUICK_REFERENCE.md",
    "implementation-status": "IMPLEMENTATION_STATUS.md",
    "enhancement-implementation": "ENHANCEMENT_IMPLEMENTATION_SUMMARY.md",
    "production-readiness": "PRODUCTION_READINESS_ANALYSIS.md",
    "contributing": "CONTRIBUTING.md",
    "git-workflow": "GIT_WORKFLOW.md"
}

DOCS_INFO = [
    {
        "id": "user-guide",
        "title": "User Guide",
        "description": "Complete guide for end users - Getting started, feature usage, examples",
        "file": "USER_GUIDE.md"
    },
    {
        "id": "quick-reference",
        "title": "Quick Reference Card",
        "description": "30-second start, shortcuts, troubleshooting - Print and keep!",
        "file": "QUICK_REFERENCE.md"
    },
    {
        "id": "implementation-status",
        "title": "Implementation Status Report",
        "description": "Current implementation status, test results, next steps",
        "file": "IMPLEMENTATION_STATUS.md"
    },
    {
        "id": "enhancement-implementation",
        "title": "Enhancement Implementation Guide",
        "description": "Detailed implementation, architecture, usage",
        "file": "ENHANCEMENT_IMPLEMENTATION_SUMMARY.md"
    },
    {
        "id": "production-readiness",
        "title": "Production Readiness Analysis",
        "description": "Performance analysis, improvement goals, expected effects",
        "file": "PRODUCTION_READINESS_ANALYSIS.md"
    },
    {
        "id": "contributing",
        "title": "Contributing Guide",
        "description": "Git workflow, commit rules, code style",
        "file": "CONTRIBUTING.md"
    },
    {
        "id": "git-workflow",
        "title": "Git Workflow Guide",
        "description": "Detailed Git commands, branch strategy",
        "file": "GIT_WORKFLOW.md"
    }
]


@router.get("/docs", response_class=HTMLResponse)
async def list_documentation():
    """List available documentation files"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>eDOCr Enhancement Documentation</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
                background: #f5f5f5;
            }
            h1 {
                color: #2563eb;
                border-bottom: 3px solid #2563eb;
                padding-bottom: 0.5rem;
            }
            .doc-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 1rem;
                margin-top: 2rem;
            }
            .doc-card {
                background: white;
                border-radius: 8px;
                padding: 1.5rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: transform 0.2s, box-shadow 0.2s;
                text-decoration: none;
                color: inherit;
                display: block;
            }
            .doc-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .doc-card h3 {
                margin: 0 0 0.5rem 0;
                color: #1e40af;
            }
            .doc-card p {
                margin: 0;
                color: #64748b;
                font-size: 0.9rem;
            }
            .back-link {
                display: inline-block;
                margin-top: 1rem;
                color: #2563eb;
                text-decoration: none;
            }
            .back-link:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>eDOCr Enhancement Documentation</h1>
        <p>Enhanced OCR system implementation documents</p>

        <div class="doc-grid">
    """

    for doc in DOCS_INFO:
        html += f"""
            <a href="/api/v1/docs/{doc['id']}" class="doc-card">
                <h3>{doc['title']}</h3>
                <p>{doc['description']}</p>
            </a>
        """

    html += """
        </div>
        <a href="/" class="back-link">Back to API root</a>
    </body>
    </html>
    """

    return html


@router.get("/docs/{doc_id}", response_class=HTMLResponse)
async def get_documentation(doc_id: str):
    """
    Get documentation as HTML

    Available docs:
    - user-guide: User guide for end users
    - quick-reference: Quick reference card
    - implementation-status: Implementation status report
    - enhancement-implementation: Enhancement implementation guide
    - production-readiness: Production readiness analysis
    - contributing: Contribution guidelines
    - git-workflow: Git workflow guide
    """
    if doc_id not in DOCS_MAP:
        raise HTTPException(status_code=404, detail="Documentation not found")

    doc_path = Path("/home/uproot/ax/poc") / DOCS_MAP[doc_id]

    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Documentation file not found")

    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'codehilite']
        )

        # Wrap in nice HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{DOCS_MAP[doc_id]} - eDOCr Documentation</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 2rem;
                    line-height: 1.6;
                    background: #f9fafb;
                }}
                .content {{
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #1e40af;
                    border-bottom: 3px solid #2563eb;
                    padding-bottom: 0.5rem;
                }}
                h2 {{
                    color: #1e40af;
                    border-bottom: 2px solid #e5e7eb;
                    padding-bottom: 0.3rem;
                    margin-top: 2rem;
                }}
                h3 {{
                    color: #3b82f6;
                }}
                code {{
                    background: #f3f4f6;
                    padding: 0.2rem 0.4rem;
                    border-radius: 4px;
                    font-size: 0.9em;
                }}
                pre {{
                    background: #1e293b;
                    color: #e2e8f0;
                    padding: 1rem;
                    border-radius: 6px;
                    overflow-x: auto;
                }}
                pre code {{
                    background: none;
                    padding: 0;
                    color: inherit;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1rem 0;
                }}
                th, td {{
                    border: 1px solid #e5e7eb;
                    padding: 0.75rem;
                    text-align: left;
                }}
                th {{
                    background: #f3f4f6;
                    font-weight: 600;
                }}
                tr:nth-child(even) {{
                    background: #f9fafb;
                }}
                .back-link {{
                    display: inline-block;
                    margin-bottom: 1rem;
                    color: #2563eb;
                    text-decoration: none;
                    font-weight: 500;
                }}
                .back-link:hover {{
                    text-decoration: underline;
                }}
                blockquote {{
                    border-left: 4px solid #2563eb;
                    padding-left: 1rem;
                    margin-left: 0;
                    color: #64748b;
                }}
            </style>
        </head>
        <body>
            <a href="/api/v1/docs" class="back-link">Back to documentation list</a>
            <div class="content">
                {html_content}
            </div>
        </body>
        </html>
        """

        return html

    except Exception as e:
        logger.error(f"Failed to read documentation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
