#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { crank, reconcile } from './lib/board_crank.mjs';
import { loadProductionPorts } from './lib/board_crank_ports.mjs';

const args = process.argv.slice(2);
if (args.includes('--help') || !args.length) {
  console.log(`Usage: momo-board-crank.mjs inspect|execute|reconcile --config /runtime/board-crank.json
  --pilot-root /source/pilot --bloodbank-root /source/bloodbank [--replay]

inspect is read-only (also --dry-run). execute requires an enabled input contract,
an accepted deployment receipt, fresh worker truth, and the existing shared lease.
--replay publishes ONLY the previously journaled exact command after revalidation.
reconcile retires only a completed fence with matching receipt, fresh no-worker
truth and final Done state. execute also reconciles an active prior execution.
No cron is installed. Runtime/contractor prerequisites are never enabled here.`);
  process.exit(0);
}
const operation = args.shift();
const flags = {};
let watchdog;
try {
  if (!['inspect', 'execute', 'reconcile'].includes(operation)) throw new Error('unknown operation');
  while (args.length) {
    const key = args.shift();
    if (['--replay', '--dry-run'].includes(key)) flags[key] = true;
    else if (['--config', '--pilot-root', '--bloodbank-root'].includes(key) && args.length) flags[key] = args.shift();
    else throw new Error('invalid arguments');
  }
  if (!flags['--config'] || !flags['--pilot-root'] || !flags['--bloodbank-root']) throw new Error('explicit config and dependency source roots required');
  const config = JSON.parse(readFileSync(resolve(flags['--config']), 'utf8'));
  if (!config.project?.workdir) throw new Error('explicit workdir required');
  process.chdir(config.project.workdir);
  // Killing a wedged pass cannot erase its fsynced intent. Its short driver
  // lease expires; its durable implementation fence never expires by TTL.
  watchdog = setTimeout(() => {
    console.log(JSON.stringify({ contract: 'board.crank.v1', status: 'uncertain',
      reason: 'control pass budget exhausted; inspect the durable journal before replay', live_execution_proof: false }));
    process.exit(124);
  }, 45000);
  const ports = await loadProductionPorts({ pilotRoot: resolve(flags['--pilot-root']),
    bloodbankRoot: resolve(flags['--bloodbank-root']), sourceRoot: resolve(dirname(fileURLToPath(import.meta.url)), '../..') });
  const result = operation === 'reconcile' ? await reconcile(config, ports, { execute: !flags['--dry-run'] }) :
    await crank(config, ports, { execute: operation === 'execute' && !flags['--dry-run'], replay: flags['--replay'] === true });
  clearTimeout(watchdog);
  console.log(JSON.stringify(result, null, 2));
  process.exitCode = ['refused', 'uncertain'].includes(result.status) ? 78 : 0;
} catch {
  clearTimeout(watchdog);
  // Dependency, vault and provider diagnostics may carry resolved credentials.
  console.log(JSON.stringify({ contract: 'board.crank.v1', status: 'refused',
    reason: 'invalid input or unavailable dependency/runtime; no activation performed', live_execution_proof: false }));
  process.exitCode = 78;
}
