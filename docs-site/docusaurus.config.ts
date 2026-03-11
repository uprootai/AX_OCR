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
  baseUrl: '/docs/',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'throw',

  i18n: {
    defaultLocale: 'ko',
    locales: ['ko'],
  },

  markdown: {
    format: 'detect',
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
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
          title: 'Core',
          items: [
            {label: 'System Overview', to: '/system-overview'},
            {label: 'Analysis Pipeline', to: '/analysis-pipeline'},
            {label: 'BlueprintFlow', to: '/blueprintflow'},
            {label: 'API Reference', to: '/api-reference'},
          ],
        },
        {
          title: 'Systems',
          items: [
            {label: 'Agent Verification', to: '/agent-verification'},
            {label: 'BOM & Quoting', to: '/bom-generation'},
            {label: 'P&ID Analysis', to: '/pid-analysis'},
            {label: 'R&D Research', to: '/research'},
          ],
        },
        {
          title: 'Operations',
          items: [
            {label: 'DevOps', to: '/devops'},
            {label: 'Deployment', to: '/deployment'},
            {label: 'Developer Guide', to: '/developer'},
            {label: 'Quality Assurance', to: '/quality-assurance'},
            {label: 'Customer Cases', to: '/customer-cases'},
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
