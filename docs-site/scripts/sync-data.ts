/**
 * sync-data.ts - Sync source code data to docs-site JSON files
 *
 * Usage: npx ts-node scripts/sync-data.ts
 *
 * This script reads key configuration files from the AX POC project
 * and generates JSON data files for the documentation site.
 */

import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(__dirname, '..', '..');

interface ServiceInfo {
  id: string;
  name: string;
  port: number;
  category: string;
  gpu: boolean;
  description: string;
  container: string;
}

function syncServices(): void {
  const registryPath = path.join(ROOT, 'web-ui/src/config/apiRegistry.ts');
  const outputPath = path.join(__dirname, '..', 'src/data/services.json');

  if (!fs.existsSync(registryPath)) {
    console.log('⚠️  apiRegistry.ts not found, skipping service sync');
    return;
  }

  const content = fs.readFileSync(registryPath, 'utf-8');

  // Extract service entries using regex (simplified parser)
  const services: ServiceInfo[] = [];
  const entryRegex = /(\w+):\s*\{[^}]*name:\s*['"]([^'"]+)['"][^}]*port:\s*(\d+)[^}]*category:\s*['"](\w+)['"][^}]*description:\s*['"]([^'"]+)['"][^}]*\}/gs;

  let match;
  while ((match = entryRegex.exec(content)) !== null) {
    services.push({
      id: match[1],
      name: match[2],
      port: parseInt(match[3]),
      category: match[4],
      gpu: content.includes(`gpu: true`) ? true : false, // simplified
      description: match[5],
      container: `${match[1].replace(/_/g, '-')}-api`,
    });
  }

  if (services.length > 0) {
    fs.writeFileSync(outputPath, JSON.stringify(services, null, 2));
    console.log(`✅ Synced ${services.length} services to services.json`);
  } else {
    console.log('⚠️  No services found in apiRegistry.ts');
  }
}

function syncMetrics(): void {
  const outputPath = path.join(__dirname, '..', 'src/data/metrics.json');

  // Count files in key directories
  const metrics = {
    lastSync: new Date().toISOString(),
    services: countJsonEntries(path.join(__dirname, '..', 'src/data/services.json')),
    nodes: countJsonEntries(path.join(__dirname, '..', 'src/data/nodes.json')),
  };

  fs.writeFileSync(outputPath, JSON.stringify(metrics, null, 2));
  console.log(`✅ Synced metrics: ${JSON.stringify(metrics)}`);
}

function countJsonEntries(filePath: string): number {
  try {
    const content = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    return Array.isArray(content) ? content.length : 0;
  } catch {
    return 0;
  }
}

// Main
console.log('🔄 Syncing AX POC data to docs-site...\n');
syncServices();
syncMetrics();
console.log('\n✅ Sync complete!');
