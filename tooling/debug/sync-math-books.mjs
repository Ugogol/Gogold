#!/usr/bin/env node
/**
 * sync-math-books — copie les Books canoniques d'un jeu Math vers son app.
 *
 * LECTURE SEULE sur `math/`. Le script ne fabrique aucun résultat, ne complète
 * aucun event, ne corrige aucun Book : il valide et il copie. Un Book qui ne
 * respecte pas le contrat fait ÉCHOUER la synchronisation — il n'est jamais
 * réparé côté frontend.
 *
 * Entrée  : math/games/<id>/canonical_books/index.json + les Books qu'il liste
 * Sortie  : <out>/<name>.json   copies conformes
 *           <out>/index.ts      module GÉNÉRÉ, à ne pas éditer à la main
 *
 * Usage :
 *   node tooling/debug/sync-math-books.mjs \
 *       --math-game math/games/0_0_plant_vs_wild \
 *       --config    apps/plant-vs-wild/src/dev/mathBooks.config.json \
 *       --out       apps/plant-vs-wild/src/dev/generated-books
 *
 * Outil du monorepo : aucun nom propre à un jeu ici. Les dimensions du plateau,
 * les types d'events autorisés et les scénarios exposés vivent dans le fichier
 * de configuration, à côté du Debug Panel de l'app.
 *
 * Aucune dépendance : Node >= 22.
 */

import { readdir, readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { join, relative, resolve } from 'node:path';

const BOOKS_DIR = 'canonical_books';

function parseArgs(argv) {
	const args = {};
	for (let index = 0; index < argv.length; index += 2) {
		const key = argv[index];
		if (!key.startsWith('--')) throw new Error(`Argument inattendu : ${key}`);
		args[key.slice(2)] = argv[index + 1];
	}
	for (const required of ['math-game', 'config', 'out']) {
		if (!args[required]) throw new Error(`Argument manquant : --${required}`);
	}
	return args;
}

// ── Validation du contrat ────────────────────────────────────────────────────

/**
 * Une Position Stake : `{reel, row}` sur un reel PADDÉ.
 *
 * La ligne 0 du book est le padding haut, les lignes 1 à `visibleRows` sont
 * visibles. Une position hors de cette plage désigne une case que le joueur ne
 * verra jamais — c'est une erreur de Book, pas une tolérance.
 */
function isPosition(value) {
	return (
		value !== null &&
		typeof value === 'object' &&
		!Array.isArray(value) &&
		typeof value.reel === 'number' &&
		typeof value.row === 'number' &&
		Object.keys(value).length === 2
	);
}

function checkPosition(position, board, where, fail) {
	if (!Number.isInteger(position.reel) || position.reel < 0 || position.reel >= board.reels) {
		fail(`${where} : reel ${position.reel} hors du plateau (0..${board.reels - 1})`);
	}
	if (!Number.isInteger(position.row) || position.row < 1 || position.row > board.visibleRows) {
		fail(`${where} : row ${position.row} hors des lignes visibles (1..${board.visibleRows})`);
	}
}

function checkSymbolGrid(value, board, rows, where, fail) {
	if (!Array.isArray(value) || value.length !== board.reels) {
		fail(`${where} : ${Array.isArray(value) ? value.length : typeof value} colonnes, ${board.reels} attendues`);
		return;
	}
	value.forEach((column, reel) => {
		if (!Array.isArray(column) || (rows !== null && column.length !== rows)) {
			fail(`${where}[${reel}] : ${column?.length} lignes, ${rows} attendues`);
			return;
		}
		column.forEach((cell, row) => {
			if (cell === null || typeof cell !== 'object' || typeof cell.name !== 'string') {
				fail(`${where}[${reel}][${row}] : symbole sans nom`);
			}
		});
	});
}

/**
 * Parcourt un event et valide tout ce qui est reconnaissable structurellement.
 *
 * Les noms de champs sont ceux du SDK Stake : `board` est un plateau paddé,
 * `newSymbols` une liste par reel, `gridMultipliers` la grille visible, et tout
 * `{reel, row}` est une Position. Aucune règle de jeu n'est appliquée ici.
 */
function checkEvent(event, board, where, fail) {
	for (const [key, value] of Object.entries(event)) {
		const path = `${where}.${key}`;

		if (key === 'board') {
			checkSymbolGrid(value, board, board.paddedRows, path, fail);
		} else if (key === 'newSymbols') {
			checkSymbolGrid(value, board, null, path, fail);
		} else if (key === 'gridMultipliers') {
			if (!Array.isArray(value) || value.length !== board.reels) {
				fail(`${path} : ${value?.length} colonnes, ${board.reels} attendues`);
			} else {
				value.forEach((column, reel) => {
					if (!Array.isArray(column) || column.length !== board.visibleRows) {
						fail(`${path}[${reel}] : ${column?.length} lignes, ${board.visibleRows} attendues`);
					} else if (column.some((cell) => typeof cell !== 'number')) {
						fail(`${path}[${reel}] : multiplicateur non numérique`);
					}
				});
			}
		} else if (isPosition(value)) {
			checkPosition(value, board, path, fail);
		} else if (Array.isArray(value) && value.every(isPosition) && value.length > 0) {
			value.forEach((position, index) => checkPosition(position, board, `${path}[${index}]`, fail));
		} else if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
			checkEvent(value, board, path, fail);
		} else if (Array.isArray(value) && value.every((item) => item && typeof item === 'object')) {
			value.forEach((item, index) => checkEvent(item, board, `${path}[${index}]`, fail));
		}
	}
}

function validateBook(name, book, config, problems) {
	const fail = (message) => problems.push(`${name} — ${message}`);
	const { board, allowedEvents } = config;

	if (!Array.isArray(book.events)) {
		fail('aucun tableau `events`');
		return;
	}

	book.events.forEach((event, index) => {
		if (typeof event.type !== 'string' || !allowedEvents.includes(event.type)) {
			fail(`event ${index} : type inconnu du contrat frontend (${event.type})`);
		}
		if (event.index !== index) {
			fail(`event ${index} : champ index = ${event.index}`);
		}
		checkEvent(event, board, `event ${index} (${event.type})`, fail);
	});

	const types = book.events.map((event) => event.type);
	const finalWins = types.filter((type) => type === 'finalWin').length;
	if (finalWins !== 1) {
		fail(`${finalWins} finalWin, exactement 1 attendu`);
	} else if (types[types.length - 1] !== 'finalWin') {
		fail('finalWin n\'est pas le dernier event');
	}

	if (config.oneSetTotalWinPerReveal) {
		const reveals = types.filter((type) => type === 'reveal').length;
		const totals = types.filter((type) => type === 'setTotalWin').length;
		if (reveals !== totals) {
			fail(`${totals} setTotalWin pour ${reveals} reveal — un par spin attendu`);
		}
	}
}

// ── Génération ───────────────────────────────────────────────────────────────

function generateIndex(entries, generic, source) {
	const imports = entries
		.map((entry) => `import ${entry.identifier} from './${entry.name}.json';`)
		.join('\n');

	const scenarios = entries
		.map(
			(entry) =>
				`\t{\n\t\tid: '${entry.name}',\n\t\tlabel: ${JSON.stringify(entry.label)},\n` +
				`\t\tpayoutMultiplier: ${entry.payoutMultiplier},\n\t\tevents: eventsOf(${entry.identifier}),\n\t},`,
		)
		.join('\n');

	const genericList = generic.map((name) => `'${name}'`).join(', ');

	return `// ⚠️ FICHIER GÉNÉRÉ — NE PAS ÉDITER À LA MAIN.
//
// Produit par \`tooling/debug/sync-math-books.mjs\` à partir de :
//   ${source}
//
// Régénérer :
//   pnpm --filter=<app> run sync:math-books
//
// Les Books sont ceux du Math SDK, copiés SANS transformation. Le frontend ne
// recalcule rien : il les rejoue par le pipeline Stake normal.
import type { BookEvent } from '../../game/typesBookEvent';

${imports}

/**
 * Unique frontière de typage entre le JSON du Math et le contrat frontend.
 *
 * Un import JSON n'a pas de type littéral : TypeScript en déduit \`string\` là où
 * le contrat attend une union. La conformité réelle est vérifiée AVANT la copie
 * par le script de synchronisation, qui échoue si un Book s'en écarte.
 */
const eventsOf = (book: { events: unknown[] }): BookEvent[] => book.events as BookEvent[];

export type MathBook = {
	id: string;
	label: string;
	payoutMultiplier: number;
	events: BookEvent[];
};

export const mathBooks: MathBook[] = [
${scenarios}
];

/** Série déterministe pour le bouton NEXT MATH. Aucun tirage. */
export const genericMathSpinIds: string[] = [${genericList}];
`;
}

// ── Programme ────────────────────────────────────────────────────────────────

async function main() {
	const args = parseArgs(process.argv.slice(2));
	const root = process.cwd();
	const booksDir = resolve(root, args['math-game'], BOOKS_DIR);
	const outDir = resolve(root, args.out);

	const config = JSON.parse(await readFile(resolve(root, args.config), 'utf8'));
	for (const key of ['board', 'allowedEvents', 'scenarios']) {
		if (!config[key]) throw new Error(`Configuration incomplète : \`${key}\` manquant.`);
	}

	let index;
	try {
		index = JSON.parse(await readFile(join(booksDir, 'index.json'), 'utf8'));
	} catch {
		throw new Error(
			`Books canoniques introuvables : ${relative(root, join(booksDir, 'index.json'))}\n` +
				`Les produire d'abord : python games/<id>/make_books.py (depuis math/)`,
		);
	}

	const available = new Map(index.books.map((entry) => [entry.name, entry]));
	const problems = [];
	const entries = [];

	for (const scenario of config.scenarios) {
		if (!available.has(scenario.name)) {
			problems.push(`${scenario.name} — absent de canonical_books/index.json`);
			continue;
		}

		const raw = await readFile(join(booksDir, `${scenario.name}.json`), 'utf8');
		const book = JSON.parse(raw);
		validateBook(scenario.name, book, config, problems);

		entries.push({
			name: scenario.name,
			label: scenario.label,
			identifier: scenario.name.replace(/[^a-zA-Z0-9]+(.)/g, (_, chr) => chr.toUpperCase()),
			payoutMultiplier: book.payoutMultiplier,
			raw,
		});
	}

	const generic = config.genericSeries ?? config.scenarios.map((scenario) => scenario.name);
	for (const name of generic) {
		if (!config.scenarios.some((scenario) => scenario.name === name)) {
			problems.push(`genericSeries : ${name} n'est pas un scénario déclaré`);
		}
	}

	if (problems.length > 0) {
		console.error(`\n✗ ${problems.length} problème(s) de contrat — rien n'a été écrit.\n`);
		problems.forEach((problem) => console.error(`  ${problem}`));
		console.error(
			'\nUn Book non conforme se corrige dans le Math, jamais dans le frontend.\n' +
				'Voir apps/<app>/src/game/typesBookEvent.ts pour le contrat attendu.\n',
		);
		process.exitCode = 1;
		return;
	}

	await mkdir(outDir, { recursive: true });

	// Les copies obsolètes disparaissent : le dossier reflète exactement l'index.
	const keep = new Set(entries.map((entry) => `${entry.name}.json`));
	for (const file of await readdir(outDir).catch(() => [])) {
		if (file.endsWith('.json') && !keep.has(file)) {
			await rm(join(outDir, file));
			console.log(`  − ${file}`);
		}
	}

	for (const entry of entries) {
		await writeFile(join(outDir, `${entry.name}.json`), entry.raw, 'utf8');
		console.log(`  ✓ ${entry.name.padEnd(24)} ${JSON.parse(entry.raw).events.length} events`);
	}

	await writeFile(
		join(outDir, 'index.ts'),
		generateIndex(entries, generic, relative(root, booksDir).replace(/\\/g, '/')),
		'utf8',
	);

	console.log(`\n${entries.length} Books synchronisés vers ${relative(root, outDir)}\n`);
}

main().catch((error) => {
	console.error(`\n✗ ${error.message}\n`);
	process.exitCode = 1;
});
