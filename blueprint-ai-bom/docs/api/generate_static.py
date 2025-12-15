#!/usr/bin/env python3
"""
Static HTML generator for documentation site
Embeds markdown content directly into HTML to avoid fetch issues
"""

import os
import json

def read_markdown_file(filename):
    """Read markdown file and return content"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def escape_for_js(text):
    """Escape text for JavaScript string"""
    return (text
            .replace('\\', '\\\\')
            .replace('`', '\\`')
            .replace('${', '\\${')
            .replace('\n', '\\n')
            .replace('\r', '\\r')
            .replace('"', '\\"')
            .replace("'", "\\'"))

def generate_static_html():
    """Generate static HTML with embedded markdown content"""

    # Read all markdown files
    markdown_files = {
        'dino-x': 'dino-x.md',
        'sam2': 'sam2.md',
        'vectorgraphnet': 'vectorgraphnet.md',
        'gat-cadnet': 'gat-cadnet.md',
        'rt-detr': 'rt-detr.md',
        'yolov11': 'yolov11.md',
        'document-transformer': 'document-transformer.md',
        'recommendations': 'recommendations.md',
        'comparison': 'comparison.md'
    }

    markdown_content = {}
    for key, filename in markdown_files.items():
        content = read_markdown_file(filename)
        markdown_content[key] = escape_for_js(content)

    # Read the template HTML
    with open('enhanced_index_backup.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Find the script section and replace the loadMarkdownContent function
    script_replacement = f'''
        // Embedded markdown content
        const markdownContent = {{
            'dino-x': `{markdown_content['dino-x']}`,
            'sam2': `{markdown_content['sam2']}`,
            'vectorgraphnet': `{markdown_content['vectorgraphnet']}`,
            'gat-cadnet': `{markdown_content['gat-cadnet']}`,
            'rt-detr': `{markdown_content['rt-detr']}`,
            'yolov11': `{markdown_content['yolov11']}`,
            'document-transformer': `{markdown_content['document-transformer']}`,
            'recommendations': `{markdown_content['recommendations']}`,
            'comparison': `{markdown_content['comparison']}`
        }};

        function loadMarkdownContent(contentType) {{
            if (contentType === 'overview') {{
                showOverview();
                return;
            }}

            const content = markdownContent[contentType];
            if (content) {{
                const htmlContent = markdownToHtml(content);
                contentDisplay.innerHTML = htmlContent;
                overviewContent.style.display = 'none';
                contentDisplay.style.display = 'block';
                backButton.style.display = 'block';
                contentDisplay.scrollTop = 0;
            }} else {{
                contentDisplay.innerHTML = `
                    <h1>📄 ${{contentType.toUpperCase()}}</h1>
                    <p style="color: #d9534f;">문서를 찾을 수 없습니다.</p>
                `;
                overviewContent.style.display = 'none';
                contentDisplay.style.display = 'block';
                backButton.style.display = 'block';
            }}
        }}
    '''

    # Find the closing script tag and insert the embedded content before it
    import re

    # Insert the embedded content and functions into the script section
    script_insertion = f'''
        const overviewContent = document.querySelector('.overview-content');
        const contentDisplay = document.getElementById('content-display');
        const backButton = document.querySelector('.back-to-main');

        // Embedded markdown content
        const markdownContent = {{}};
        {chr(10).join([f"        markdownContent['{key}'] = {json.dumps(content, ensure_ascii=False)};" for key, content in markdown_content.items()])}

        // Markdown to HTML conversion
        let mermaidCounter = 0;
        function markdownToHtml(markdown) {{
            let html = markdown;

            // Mermaid diagrams (before code blocks)
            const mermaidRegex = /```mermaid\\n([\\s\\S]*?)```/g;
            html = html.replace(mermaidRegex, (match, diagram) => {{
                const id = `mermaid-diagram-${{mermaidCounter++}}`;
                return `<div class="mermaid" id="${{id}}">${{diagram.trim()}}</div>`;
            }});

            // Headers
            html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
            html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
            html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

            // Bold and italic
            html = html.replace(/\\*\\*\\*(.*?)\\*\\*\\*/gim, '<strong><em>$1</em></strong>');
            html = html.replace(/\\*\\*(.*?)\\*\\*/gim, '<strong>$1</strong>');
            html = html.replace(/\\*(.*?)\\*/gim, '<em>$1</em>');

            // Code blocks (after mermaid)
            html = html.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');
            html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

            // Lists
            html = html.replace(/^\\* (.+)$/gim, '<li>$1</li>');
            html = html.replace(/(<li>.*<\\/li>)/s, '<ul>$1</ul>');
            html = html.replace(/^\\d+\\. (.+)$/gim, '<li>$1</li>');

            // Links
            html = html.replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" target="_blank">$1</a>');

            // Images
            html = html.replace(/!\\[([^\\]]*)\\]\\(([^)]+)\\)/g, '<img src="$2" alt="$1" style="max-width: 100%; height: auto;">');

            // Paragraphs
            html = html.replace(/\\n\\n/g, '</p><p>');
            html = '<p>' + html + '</p>';

            // Clean up
            html = html.replace(/<p><\\/p>/g, '');
            html = html.replace(/<p>(<h[1-6]>)/g, '$1');
            html = html.replace(/(<\\/h[1-6]>)<\\/p>/g, '$1');
            html = html.replace(/<p>(<div class="mermaid")/g, '$1');
            html = html.replace(/(<\\/div>)<\\/p>/g, '$1');

            return html;
        }}

        // Load markdown content
        function loadMarkdownContent(contentType) {{
            if (contentType === 'overview') {{
                showOverview();
                return;
            }}

            const content = markdownContent[contentType];
            if (content) {{
                const htmlContent = markdownToHtml(content);
                contentDisplay.innerHTML = htmlContent;
                overviewContent.style.display = 'none';
                contentDisplay.style.display = 'block';
                backButton.style.display = 'block';
                contentDisplay.scrollTop = 0;

                // Reinitialize Mermaid for the new content
                if (typeof mermaid !== 'undefined') {{
                    mermaid.init(undefined, contentDisplay.querySelectorAll('.mermaid'));
                }}
            }} else {{
                contentDisplay.innerHTML = `
                    <div class="alert alert-danger">
                        <h4>⚠️ Content Not Found</h4>
                        <p>The requested content could not be found.</p>
                    </div>
                `;
                overviewContent.style.display = 'none';
                contentDisplay.style.display = 'block';
                backButton.style.display = 'block';
            }}
        }}

        // Show overview
        function showOverview() {{
            overviewContent.style.display = 'block';
            contentDisplay.style.display = 'none';
            backButton.style.display = 'none';
        }}

        // Event listeners
        document.querySelectorAll('.nav-item').forEach(link => {{
            link.addEventListener('click', (e) => {{
                e.preventDefault();
                const contentType = link.getAttribute('data-content');

                // Update active state
                document.querySelectorAll('.nav-item').forEach(item => {{
                    item.classList.remove('active');
                }});
                link.classList.add('active');

                loadMarkdownContent(contentType);
            }});
        }});

        // Back button
        backButton.addEventListener('click', () => {{
            showOverview();
            document.querySelectorAll('.nav-item').forEach(item => {{
                item.classList.remove('active');
            }});
            document.querySelector('.nav-item[data-content="overview"]').classList.add('active');
        }});

        // Model cards click
        document.querySelectorAll('.model-card').forEach(card => {{
            card.addEventListener('click', () => {{
                const contentType = card.getAttribute('data-content');
                loadMarkdownContent(contentType);

                // Update nav
                document.querySelectorAll('.nav-item').forEach(item => {{
                    item.classList.remove('active');
                    if (item.getAttribute('data-content') === contentType) {{
                        item.classList.add('active');
                    }}
                }});
            }});
        }});

        // Initialize
        showOverview();
    '''

    # Replace the script tag
    html_content = html_content.replace('    <script>', f'    <script>\n{script_insertion}')

    # Write the static HTML
    with open('index_static.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("Static HTML generated: index_static.html")

if __name__ == '__main__':
    generate_static_html()