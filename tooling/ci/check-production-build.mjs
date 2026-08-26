#!/usr/bin/env node
/**
 * check-production-build — garde-fou sur le build de production d'une app.
 *
 * 1. BLOQUANT  : aucun marqueur de développement ne doit survivre dans le build
 *                (Debug Panel, fixtures DEV, bypass RGS local — voir docs/DEBUG_PANEL.md).
 * 2. INFORMATIF : mesure RUNTIME ASSETS SIZE et FINAL FRONTEND BUILD SIZE.
 *
 * Découvre automatiquement les apps possédant un `build/` : une future slot est
 * couverte sans modifier ce script.
 *
 * Usage :
 *   node tooling/ci/check-production-build.mjs            # toutes les apps buildées
 *   node tooling/ci/check-production-build.mjs apps/lines # une app précise
 *
 * Sortie : 1 si un marqueur est trouvé, 2 si aucun build à contrôler, sinon 0.
 * Aucune dépendance : Node >= 22.
 */

import { readdir, stat, readFile, appendFile } from 'node:fs/promises';
import { join, relative, basename } from 'node:path';

/**
 * Marqueurs communs à toutes les apps.
 *
 * Ce script est un outil du monorepo : il ne doit contenir aucun nom propre à un
 * jeu. Une app qui possède son propre outillage DEV déclare ses marqueurs dans
 * `apps/<app>/dev-markers.json` — un simple tableau de chaînes — et ils sont
 * ajoutés à cette liste pour cette app uniquement.
 */
const FORBIDDEN_MARKERS = [
	'DebugPanel',
	'debugScenarios',
	'isLocalDebugMode',
	'DEBUG_QUERY_KEY',
];

/** Marqueurs déclarés par l'app elle-même. Fichier optionnel. */
async function readAppMarkers(appDir) {
	try {
		const raw = await readFile(join(appDir, 'dev-markers.json'), 'utf8');
		const parsed = JSON.parse(raw);
		if (!Array.isArray(parsed) || parsed.some((marker) => typeof marker !== 'string')) {
			console.error(`  ⚠ ${appDir}/dev-markers.json ignoré : un tableau de chaînes est attendu.`);
			return [];
		}
		return parsed;
	} catch {
		return [];
	}
}

/** Seuls les fichiers texte sont scannés — le reste du build est binaire. */
const TEXT_EXTENSIONS = new Set(['.html', '.js', '.mjs', '.cjs', '.css', '.json', '.map', '.txt']);

const BYTE_UNITS = ['B', 'KB', 'MB', 'GB'];

function formatBytes(bytes) {
	let value = bytes;
	let unit = 0;
	while (value >= 1024 && unit < BYTE_UNITS.length - 1) {
		value /= 1024;
		unit += 1;
	}
	return `${value.toFixed(unit === 0 ? 0 : 1)} ${BYTE_UNITS[unit]}`;
}

async function walk(dir, onFile) {
	let entries;
	try {
		entries = await readdir(dir, { withFileTypes: true });
	} catch {
		return;
	}
	for (const entry of entries) {
		const full = join(dir, entry.name);
		if (entry.isDirectory()) await walk(full, onFile);
		else if (entry.isFile()) await onFile(full);
	}
}

async function directorySize(dir) {
	let total = 0;
	await walk(dir, async (file) => {
		total += (await stat(file)).size;
	});
	return total;
}

/** Cherche les marqueurs interdits dans les fichiers texte du build. */
async function findMarkers(buildDir, markers) {
	const hits = [];
	await walk(buildDir, async (file) => {
		const dot = file.lastIndexOf('.');
		if (dot === -1 || !TEXT_EXTENSIONS.has(file.slice(dot).toLowerCase())) return;
		const content = await readFile(file, 'utf8');
		for (const marker of markers) {
			if (content.includes(marker)) hits.push({ file: relative(buildDir, file), marker });
		}
	});
	return hits;
}

/** Apps possédant un build/ — découverte automatique. */
async function findBuiltApps(explicit) {
	if (explicit) return [explicit];
	const apps = [];
	let entries;
	try {
		entries = await readdir('apps', { withFileTypes: true });
	} catch {
		return apps;
	}
	for (const entry of entries) {
		if (!entry.isDirectory()) continue;
		const appDir = join('apps', entry.name);
		try {
			if ((await stat(join(appDir, 'build'))).isDirectory()) apps.push(appDir);
		} catch {
			/* pas de build : app non buildée ou placeholder */
		}
	}
	return apps;
}

async function writeSummary(rows) {
	const file = process.env.GITHUB_STEP_SUMMARY;
	if (!file) return;
	const lines = [
		'### Taille des builds frontend',
		'',
		'| App | Runtime assets | Build final |',
		'| --- | ---: | ---: |',
		...rows.map((r) => `| \`${r.app}\` | ${r.assets} | ${r.build} |`),
		'',
		'> Mesuré, non bloquant. Les budgets stricts seront définis pour les vraies slots.',
		'',
	];
	await appendFile(file, lines.join('\n'));
}

async function main() {
	const explicit = process.argv[2];
	const apps = await findBuiltApps(explicit);

	if (apps.length === 0) {
		console.error("Aucune app buildée trouvée. Lancer `pnpm run build` d'abord.");
		process.exit(2);
	}

	const rows = [];
	let failed = false;

	for (const appDir of apps) {
		const buildDir = join(appDir, 'build');
		const assetsDir = join(appDir, 'static', 'assets');

		const markers = [...FORBIDDEN_MARKERS, ...(await readAppMarkers(appDir))];

		const [buildSize, assetsSize, hits] = await Promise.all([
			directorySize(buildDir),
			directorySize(assetsDir),
			findMarkers(buildDir, markers),
		]);

		console.log(`\n${appDir}`);
		console.log(`  RUNTIME ASSETS SIZE       ${formatBytes(assetsSize)}`);
		console.log(`  FINAL FRONTEND BUILD SIZE ${formatBytes(buildSize)}`);

		if (hits.length > 0) {
			failed = true;
			console.log(`  ✗ ${hits.length} marqueur(s) de développement dans le build :`);
			for (const hit of hits) console.log(`      ${hit.marker} → ${hit.file}`);
		} else {
			console.log(`  ✓ aucun marqueur de développement (${markers.join(', ')})`);
		}

		rows.push({
			app: basename(appDir),
			assets: formatBytes(assetsSize),
			build: formatBytes(buildSize),
		});
	}

	await writeSummary(rows);

	if (failed) {
		console.error('\nÉchec : du code de développement a atteint un build de production.');
		process.exit(1);
	}
	console.log('\nBuilds de production conformes.');
}

main();
