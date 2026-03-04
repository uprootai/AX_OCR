#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const servicesPath = path.join(rootDir, 'src', 'data', 'services.json');
const catalogPath = path.join(rootDir, 'docs', 'system-overview', 'service-catalog.mdx');

const START_MARKER = '<!-- AUTO-GENERATED:START -->';
const END_MARKER = '<!-- AUTO-GENERATED:END -->';

const CATEGORY_ORDER = [
  'detection',
  'ocr',
  'segmentation',
  'preprocessing',
  'analysis',
  'knowledge',
  'ai',
  'control',
];

const CATEGORY_LABEL = {
  detection: '객체 검출(Detection)',
  ocr: '광학 문자 인식(OCR)',
  segmentation: '세그멘테이션(Segmentation)',
  preprocessing: '전처리(Preprocessing)',
  analysis: '분석(Analysis)',
  knowledge: '지식 그래프(Knowledge)',
  ai: '인공지능(AI)',
  control: '오케스트레이터(Orchestrator)',
};

function gpuLabel(isGpu) {
  return isGpu ? '사용' : '미사용';
}

function formatCategorySection(category, items) {
  const title = CATEGORY_LABEL[category] ?? category;
  const lines = [];
  lines.push(`### ${title} (${items.length}개 서비스)`);
  lines.push('');
  lines.push('| 서비스 | 포트 | GPU | 설명 |');
  lines.push('|--------|------|-----|------|');
  for (const item of items) {
    lines.push(`| **${item.name}** | ${item.port} | ${gpuLabel(item.gpu)} | ${item.description} |`);
  }
  lines.push('');
  return lines.join('\n');
}

function main() {
  const services = JSON.parse(fs.readFileSync(servicesPath, 'utf8'));
  const catalog = fs.readFileSync(catalogPath, 'utf8');

  const byCategory = new Map();
  for (const category of CATEGORY_ORDER) byCategory.set(category, []);
  for (const service of services) {
    if (!byCategory.has(service.category)) byCategory.set(service.category, []);
    byCategory.get(service.category).push(service);
  }
  for (const [, items] of byCategory) {
    items.sort((a, b) => a.port - b.port || a.name.localeCompare(b.name, 'ko'));
  }

  const generated = [];
  for (const category of CATEGORY_ORDER) {
    const items = byCategory.get(category) || [];
    if (items.length === 0) continue;
    generated.push(formatCategorySection(category, items));
  }
  const generatedBlock = `${START_MARKER}\n${generated.join('\n')}${END_MARKER}`;

  const startIdx = catalog.indexOf(START_MARKER);
  const endIdx = catalog.indexOf(END_MARKER);
  if (startIdx === -1 || endIdx === -1 || endIdx < startIdx) {
    throw new Error(`Markers not found in ${catalogPath}`);
  }

  const before = catalog.slice(0, startIdx);
  const after = catalog.slice(endIdx + END_MARKER.length);
  const next = `${before}${generatedBlock}${after}`;
  fs.writeFileSync(catalogPath, next, 'utf8');

  const gpuCount = services.filter(s => s.gpu).length;
  const cpuCount = services.length - gpuCount;
  console.log(`Updated service catalog from services.json (${services.length} services, GPU ${gpuCount}, CPU ${cpuCount})`);
}

main();
