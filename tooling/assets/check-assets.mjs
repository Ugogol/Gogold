#!/usr/bin/env node
/**
 * check-assets — mesure et valide un dossier d'assets runtime Gogold.
 *
 * Ce script LIT, ANALYSE et SIGNALE. Il ne modifie ni ne supprime jamais rien.
 * Aucune dépendance : Node >= 22 uniquement.
 *
 * Usage :
 *   node tooling/assets/check-assets.mjs apps/<game>/static/assets
 *   node tooling/assets/check-assets.mjs <dir> --json
 *
 * Code de sortie : 1 si des fichiers interdits sont détectés, sinon 0.
 */

import { readdir, stat } from 'node:fs/promises';
import { join, extname, relative, sep } from 'node:path';

/** Formats de production (MASTER) : jamais dans un dossier runtime. */
const MASTER_EXTENSIONS = new Set([
	'.psd', '.psb', '.aep', '.blend', '.blend1', '.kra', '.xcf',
	'.ai', '.clip', '.sai', '.cdr', '.afdesign', '.afphoto',
	'.wav', '.aiff', '.aif', '.flac', '.aup3', '.als', '.flp', '.logicx',
	'.spine', // projet Spine : l'export runtime est .atlas + .json/.skel
]);

/** Fichiers manifestement temporaires ou résiduels. */
const TEMP_EXTENSIONS = new Set(['.tmp', '.temp', '.bak', '.old', '.orig', '.swp', '.log']);
const TEMP_NAMES = new Set(['thumbs.db', '.ds_store', 'desktop.ini']);

/** Catégories runtime de référence (voir docs/ASSETS.md §2). */
const KNOWN_CATEGORIES = new Set(['audio', 'fonts', 'spines', 'sprites']);

const BYTE_UNITS = ['B', 'KB', 'MB', 'GB'];

function formatBytes(bytes) {
	let value = bytes;
	let unit = 0;
	while (value >= 1024 && unit < BYTE_UNITS.length - 1) {
		value /= 1024;
		unit += 1;
	}
	const digits = unit === 0 ? 0 : value < 10 ? 2 : 1;
	return `${value.toFixed(digits)} ${BYTE_UNITS[unit]}`;
}

/** Parcourt récursivement `root` et retourne la liste des fichiers. */
async function collectFiles(root) {
	const files = [];
	async function walk(dir) {
		const entries = await readdir(dir, { withFileTypes: true });
		for (const entry of entries) {
			const full = join(dir, entry.name);
			if (entry.isDirectory()) {
				await walk(full);
			} else if (entry.isFile()) {
				const { size } = await stat(full);
				const rel = relative(root, full);
				files.push({
					path: full,
					rel,
					name: entry.name,
					ext: extname(entry.name).toLowerCase(),
					category: rel.split(sep)[0] ?? '',
					size,
				});
			}
		}
	}
	await walk(root);
	return files;
}

/** Somme les tailles par clé, triées du plus lourd au plus léger. */
function groupBy(files, keyOf) {
	const totals = new Map();
	for (const file of files) {
		const key = keyOf(file) || '(racine)';
		const current = totals.get(key) ?? { count: 0, size: 0 };
		current.count += 1;
		current.size += file.size;
		totals.set(key, current);
	}
	return [...totals.entries()].sort((a, b) => b[1].size - a[1].size);
}

/** Fichiers qui n'ont rien à faire dans un dossier runtime. */
function findIssues(files) {
	const masters = files.filter((f) => MASTER_EXTENSIONS.has(f.ext));
	const temps = files.filter(
		(f) => TEMP_EXTENSIONS.has(f.ext) || TEMP_NAMES.has(f.name.toLowerCase()),
	);
	const unknownCategories = [...new Set(files.map((f) => f.category))]
		.filter((c) => c && !KNOWN_CATEGORIES.has(c))
		.sort();
	return { masters, temps, unknownCategories };
}

function renderTable(rows, total) {
	const width = Math.max(...rows.map(([key]) => key.length), 12);
	return rows
		.map(([key, { count, size }]) => {
			const share = total > 0 ? ((size / total) * 100).toFixed(1) : '0.0';
			return `  ${key.padEnd(width)}  ${formatBytes(size).padStart(10)}  ${String(count).padStart(5)} fichiers  ${share.padStart(5)} %`;
		})
		.join('\n');
}

function renderReport(root, files, issues) {
	const total = files.reduce((sum, f) => sum + f.size, 0);
	const heaviest = [...files].sort((a, b) => b.size - a.size).slice(0, 10);
	const lines = [];

	lines.push(`\nGOGOLD ASSET CHECK — ${root}`);
	lines.push('='.repeat(64));
	lines.push(`\nRUNTIME ASSETS SIZE : ${formatBytes(total)}  (${files.length} fichiers)`);

	lines.push('\nPoids par dossier principal');
	lines.push(renderTable(groupBy(files, (f) => f.category), total));

	lines.push('\nPoids par extension');
	lines.push(renderTable(groupBy(files, (f) => f.ext || '(sans extension)'), total));

	lines.push('\n10 fichiers les plus lourds');
	lines.push(
		heaviest
			.map((f, i) => `  ${String(i + 1).padStart(2)}. ${formatBytes(f.size).padStart(10)}  ${f.rel}`)
			.join('\n'),
	);

	const formats = [...new Set(files.map((f) => f.ext || '(sans extension)'))].sort();
	lines.push(`\nFormats rencontrés (${formats.length})`);
	lines.push(`  ${formats.join(' ')}`);

	lines.push('\nValidation runtime');
	lines.push(...renderIssues(issues));

	return lines.join('\n');
}

function renderIssues({ masters, temps, unknownCategories }) {
	const lines = [];
	if (masters.length > 0) {
		lines.push(`  ✗ ${masters.length} fichier(s) source/master dans un dossier runtime :`);
		lines.push(...masters.map((f) => `      ${f.rel}  (${formatBytes(f.size)})`));
	} else {
		lines.push('  ✓ aucun fichier source/master (.psd, .aep, .blend, .wav…)');
	}
	if (temps.length > 0) {
		lines.push(`  ✗ ${temps.length} fichier(s) temporaire(s)/résiduel(s) :`);
		lines.push(...temps.map((f) => `      ${f.rel}`));
	} else {
		lines.push('  ✓ aucun fichier temporaire (.tmp, .bak, Thumbs.db…)');
	}
	if (unknownCategories.length > 0) {
		lines.push(`  ! dossier(s) hors convention : ${unknownCategories.join(', ')}`);
		lines.push('      attendu : audio/ fonts/ spines/ sprites/ (docs/ASSETS.md §2)');
	} else {
		lines.push('  ✓ dossiers conformes à audio/ fonts/ spines/ sprites/');
	}
	lines.push('\nCe script ne supprime rien. Corriger les ✗ à la main avant publication.');
	return lines;
}

function buildJson(root, files, issues) {
	const total = files.reduce((sum, f) => sum + f.size, 0);
	const toObject = (rows) =>
		Object.fromEntries(rows.map(([key, { count, size }]) => [key, { count, bytes: size }]));
	return {
		root,
		totalBytes: total,
		totalFiles: files.length,
		byCategory: toObject(groupBy(files, (f) => f.category)),
		byExtension: toObject(groupBy(files, (f) => f.ext || '(sans extension)')),
		heaviest: [...files]
			.sort((a, b) => b.size - a.size)
			.slice(0, 10)
			.map((f) => ({ path: f.rel, bytes: f.size })),
		issues: {
			masterFiles: issues.masters.map((f) => f.rel),
			tempFiles: issues.temps.map((f) => f.rel),
			unknownCategories: issues.unknownCategories,
		},
	};
}

async function main() {
	const args = process.argv.slice(2);
	const asJson = args.includes('--json');
	const root = args.find((a) => !a.startsWith('--'));

	if (!root) {
		console.error('Usage: node tooling/assets/check-assets.mjs <dossier> [--json]');
		process.exit(2);
	}

	let stats;
	try {
		stats = await stat(root);
	} catch {
		console.error(`Dossier introuvable : ${root}`);
		process.exit(2);
	}
	if (!stats.isDirectory()) {
		console.error(`Ce n'est pas un dossier : ${root}`);
		process.exit(2);
	}

	const files = await collectFiles(root);
	if (files.length === 0) {
		console.error(`Aucun fichier dans : ${root}`);
		process.exit(2);
	}

	const issues = findIssues(files);
	console.log(asJson ? JSON.stringify(buildJson(root, files, issues), null, 2) : renderReport(root, files, issues));

	const blocking = issues.masters.length + issues.temps.length;
	process.exit(blocking > 0 ? 1 : 0);
}

main();
