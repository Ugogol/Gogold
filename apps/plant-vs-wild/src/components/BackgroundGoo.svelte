<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Tween } from 'svelte/motion';
	import { cubicIn, cubicOut, sineInOut } from 'svelte/easing';
	import { Container, Sprite } from 'pixi-svelte';

	import { getContext } from '../game/context';
	import { BACKGROUND_GOO, BACKGROUND_RATIO, zIndexes } from '../game/constants';
	import { backgroundRect } from '../game/utils';

	/**
	 * Glu orange qui goutte de la grande plante, à droite du décor.
	 *
	 * PUREMENT DÉCORATIF. Le composant n'écoute aucun bookEvent, ne lit aucun
	 * état de jeu et n'en écrit aucun : il ne peut donc ni révéler un round, ni
	 * interférer avec le gameplay. Il vit derrière tout le jeu (`zIndexes.
	 * background.goo`) et devant les deux fonds.
	 *
	 * ── POURQUOI DES FRACTIONS ET PAS DES PIXELS ────────────────────────────
	 * La plante est peinte DANS l'image de fond, mise à l'échelle en « cover » :
	 * sa position à l'écran dépend du viewport. Toutes les coordonnées d'ici
	 * sont donc des fractions de cette image, converties en pixels AU RENDU.
	 * Conséquence utile : un redimensionnement de fenêtre, même en pleine
	 * chute, repositionne l'effet correctement sans calcul supplémentaire.
	 *
	 * ── ANIMATION ───────────────────────────────────────────────────────────
	 * Aucune dépendance ajoutée : `Tween` de `svelte/motion`, déjà l'outil
	 * d'animation de `WildFlight`, `Symbol` et `TumbleBoard`. Aucune
	 * spritesheet, aucune vidéo — trois sprites et des transformations.
	 *
	 * L'attente entre deux gouttes est elle aussi un `Tween` awaité plutôt
	 * qu'un `setTimeout` : c'est la convention de `FreeSpinBanner`, et cela
	 * évite un timer qui survivrait au démontage.
	 *
	 * Les réglages (position, taille, fréquence, durées) sont tous dans
	 * `BACKGROUND_GOO`, dans `constants.ts`.
	 */
	const context = getContext();

	const stacked = $derived(context.stateLayoutDerived.isStacked());

	/** Rectangle du fond à l'écran : c'est le repère de tout ce qui suit. */
	const rect = $derived(
		backgroundRect(
			stacked
				? context.stateLayoutDerived.portraitBackgroundLayout({ scale: 1 })
				: context.stateLayoutDerived.normalBackgroundLayout({ scale: 1 }),
			stacked ? BACKGROUND_RATIO.portrait : BACKGROUND_RATIO.normal,
		),
	);

	/** Les fractions dépendent de l'asset de fond, donc de l'orientation. */
	const tuning = $derived(stacked ? BACKGROUND_GOO.portrait : BACKGROUND_GOO.landscape);

	// Le sprite de fond est ancré en son centre : une fraction 0.5 tombe sur `rect.x`.
	const toX = (fraction: number) => rect.x + (fraction - 0.5) * rect.width;
	const toY = (fraction: number) => rect.y + (fraction - 0.5) * rect.height;

	// ── État animé, tout en fractions ───────────────────────────────────────

	/** Respiration de la glu suspendue. */
	const breatheX = new Tween(1);
	const breatheY = new Tween(1);

	/** La goutte : position, étirement vertical et taille du tirage courant. */
	const dropY = new Tween(0);
	const dropStretch = new Tween(1);
	let dropVisible = $state(false);
	let dropOffsetX = $state(0);
	let dropSizeRatio = $state(1);

	/** L'éclaboussure. */
	const splashScale = new Tween(BACKGROUND_GOO.splashScaleFrom);
	const splashAlpha = new Tween(1);
	let splashVisible = $state(false);

	// ── Tailles à l'écran, dérivées du fond ─────────────────────────────────

	const hangWidth = $derived(rect.width * tuning.hangWidth);
	const dropWidth = $derived(rect.width * tuning.dropWidth * dropSizeRatio);
	const splashWidth = $derived(rect.width * tuning.splashWidth * dropSizeRatio);

	/** Les trois textures sont carrées sauf l'éclaboussure, plus large que haute. */
	const SPLASH_ASPECT = 512 / 288;

	// ── Boucle ──────────────────────────────────────────────────────────────

	const random = (min: number, max: number) => min + Math.random() * (max - min);

	/**
	 * Attente annulable : un `Tween` awaité, jamais un `setTimeout`.
	 *
	 * On bascule entre deux valeurs au lieu d'incrémenter `timer.current` : LIRE
	 * la valeur d'un Tween crée une dépendance réactive, et cette lecture-là
	 * relançait la boucle à chaque image. `flip` est une variable ordinaire, pas
	 * un `$state` : rien ne l'observe.
	 */
	const timer = new Tween(0);
	let flip = 0;
	const wait = (duration: number) => {
		flip = 1 - flip;
		return timer.set(flip, { duration });
	};

	const runCycle = async (isCancelled: () => boolean) => {
		while (!isCancelled()) {
			await wait(random(BACKGROUND_GOO.delay.min, BACKGROUND_GOO.delay.max));
			if (isCancelled()) return;

			// Chaque goutte diffère un peu de la précédente : sans cela, l'œil
			// repère la boucle en quelques cycles.
			dropOffsetX = random(-BACKGROUND_GOO.jitter.x, BACKGROUND_GOO.jitter.x);
			dropSizeRatio = random(1 - BACKGROUND_GOO.jitter.size, 1 + BACKGROUND_GOO.jitter.size);

			// 1. La goutte se forme sous la glu et s'étire vers le bas.
			dropY.set(tuning.anchor.y, { duration: 0 });
			dropStretch.set(1, { duration: 0 });
			dropVisible = true;
			await dropStretch.set(1.7, {
				duration: BACKGROUND_GOO.stretchDuration,
				easing: cubicOut,
			});
			if (isCancelled()) return;

			// 2. Elle se détache et tombe en accélérant — `cubicIn` EST la gravité.
			dropStretch.set(1.25, { duration: BACKGROUND_GOO.fallDuration });
			await dropY.set(tuning.ground, {
				duration: BACKGROUND_GOO.fallDuration,
				easing: cubicIn,
			});
			if (isCancelled()) return;
			dropVisible = false;

			// 3. Impact : petit scale-up et fondu, au point de chute exact.
			splashScale.set(BACKGROUND_GOO.splashScaleFrom, { duration: 0 });
			splashAlpha.set(1, { duration: 0 });
			splashVisible = true;
			await Promise.all([
				splashScale.set(1, { duration: BACKGROUND_GOO.splashDuration, easing: cubicOut }),
				splashAlpha.set(0, { duration: BACKGROUND_GOO.splashDuration }),
			]);
			splashVisible = false;
		}
	};

	const runBreathe = async (isCancelled: () => boolean) => {
		const { amplitude, duration } = BACKGROUND_GOO.breathe;
		while (!isCancelled()) {
			await Promise.all([
				breatheX.set(1 + amplitude, { duration, easing: sineInOut }),
				breatheY.set(1 - amplitude, { duration, easing: sineInOut }),
			]);
			if (isCancelled()) return;
			await Promise.all([
				breatheX.set(1 - amplitude, { duration, easing: sineInOut }),
				breatheY.set(1 + amplitude, { duration, easing: sineInOut }),
			]);
		}
	};

	/**
	 * Les deux boucles sont infinies : elles DOIVENT s'arrêter au démontage.
	 * Le drapeau est lu après chaque `await`, donc au plus tard un pas
	 * d'animation après la destruction du composant — aucun ticker orphelin.
	 *
	 * `onMount` et NON `$effect` : un effet suit les valeurs qu'il lit, et les
	 * boucles en touchent plusieurs qui changent à chaque image. Mesuré avant
	 * correction — l'effet se relançait 21 fois en 30 secondes, annulant le
	 * cycle avant qu'une seule goutte n'ait le temps de tomber. `onMount` ne
	 * suit rien : il démarre une fois, et sa fonction de retour arrête tout.
	 */
	onMount(() => {
		let cancelled = false;
		const isCancelled = () => cancelled;
		runCycle(isCancelled);
		runBreathe(isCancelled);
		return () => {
			cancelled = true;
		};
	});
</script>

<Container zIndex={zIndexes.background.goo}>
	<Sprite
		key="gooHang"
		anchor={{ x: 0.5, y: 0 }}
		x={toX(tuning.anchor.x)}
		y={toY(tuning.anchor.y)}
		width={hangWidth * breatheX.current}
		height={hangWidth * breatheY.current}
	/>

	{#if dropVisible}
		<Sprite
			key="gooDrop"
			anchor={{ x: 0.5, y: 0.5 }}
			x={toX(tuning.anchor.x + dropOffsetX)}
			y={toY(dropY.current)}
			width={dropWidth}
			height={dropWidth * dropStretch.current}
		/>
	{/if}

	{#if splashVisible}
		<Sprite
			key="gooSplash"
			anchor={{ x: 0.5, y: 1 }}
			x={toX(tuning.anchor.x + dropOffsetX)}
			y={toY(tuning.ground)}
			alpha={splashAlpha.current}
			width={splashWidth * splashScale.current}
			height={(splashWidth / SPLASH_ASPECT) * splashScale.current}
		/>
	{/if}
</Container>
