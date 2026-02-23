import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'AX POC Documentation',
  tagline: '기계 도면 자동 분석 및 제조 견적 생성 시스템',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://ax-poc-docs.example.com',
  baseUrl: '/',

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'ko',
    locales: ['ko'],
  },

  markdown: {
    mermaid: true,
  },

  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: 'docs',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/social-card.png',
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
    },
    mermaid: {
      theme: {light: 'default', dark: 'dark'},
    },
    navbar: {
      title: 'AX POC',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Documentation',
        },
        {
          href: 'http://localhost:5173',
          label: 'Web UI',
          position: 'right',
        },
        {
          href: 'http://localhost:3000',
          label: 'BOM UI',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {label: 'System Overview', to: '/docs/system-overview'},
            {label: 'Analysis Pipeline', to: '/docs/analysis-pipeline'},
            {label: 'BlueprintFlow', to: '/docs/blueprintflow'},
          ],
        },
        {
          title: 'Systems',
          items: [
            {label: 'Agent Verification', to: '/docs/agent-verification'},
            {label: 'BOM & Quoting', to: '/docs/bom-generation'},
            {label: 'P&ID Analysis', to: '/docs/pid-analysis'},
          ],
        },
        {
          title: 'Operations',
          items: [
            {label: 'Batch & Delivery', to: '/docs/batch-delivery'},
            {label: 'Quality Assurance', to: '/docs/quality-assurance'},
            {label: 'DevOps', to: '/docs/devops'},
          ],
        },
      ],
      copyright: `AX POC Documentation | Built with Docusaurus`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'python', 'yaml', 'docker'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
