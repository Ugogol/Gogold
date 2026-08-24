<script lang="ts">
	import _ from 'lodash';
	import { Container, Rectangle, Text } from 'pixi-svelte';
	import { MainContainer } from 'components-layout';
	import {
		DESKTOP_BASE_SIZE,
		TABLET_BASE_SIZE,
		LANDSCAPE_BASE_SIZE,
		PORTRAIT_BASE_SIZE,
	} from 'components-ui-pixi/src/constants';

	import { getContext } from '../game/context';
	import { getSymbolX, getSymbolY } from '../game/utils';
	import {
		SYMBOL_SIZE,
		CELL_SIZE,
		CELL_GAP,
		MOBILE_BAR,
		BOARD_SIZES,
		LAYOUT_BANDS,
		isMobileLayout,
		BOARD_DIMENSIONS,
		SYMBOL_DISPLAY_SIZE,
		type LayoutType,
	} from '../game/constants';
	import { visualGuides, visualMetrics, VISUAL_BOARD } from './visualMode.svelte';

	/**
	 * Repères de revue visuelle — DÉVELOPPEMENT UNIQUEMENT.
	 *
	 * Les bandes réservées sont ancrées aux bords du VIEWPORT, pas à ceux de
	 * l'espace de design : sur un écran plus large que l'espace (2560×1080) ou
	 * plus haut (téléphone 19,5:9), l'espace ne le remplit pas et une bande
	 * ancrée au design flotterait loin du bord.
	 *
	 * Sur desktop et tablet, un second calque dessine le bloc de boutons Stake à
	 * ses VRAIES coordonnées (`LayoutDesktop` & consorts). S'il tombe dans la
	 * bande réservée, la réservation est juste. C'est le contrôle.
	 *
	 * Sur mobile ce contrôle n'a plus lieu d'être : la barre mobile diverge
	 * volontairement de `LayoutPortrait` (voir MOBILE_BAR dans constants.ts).
	 */
	const context = getContext();

	const GUIDE = {
		design: 0x39a0ff,
		band: 0xffb020,
		grid: 0x39ff88,
		cell: 0xff3d81,
		center: 0xffffff,
		bar: 0xffb020,
		spin: 0x39ff88,
	};

	const layoutType = $derived(context.stateLayoutDerived.layoutType() as LayoutType);
	const mainLayout = $derived(context.stateLayoutDerived.mainLayout());
	const bands = $derived(LAYOUT_BANDS[layoutType]);
	const boardLayout = $derived(context.stateGameDerived.boardLayout());
	const mobile = $derived(isMobileLayout(layoutType));

	const columns = _.range(BOARD_DIMENSIONS.x);
	const rows = _.range(BOARD_DIMENSIONS.y);

	/** Bords du viewport réel, exprimés dans l'espace de design du jeu. */
	const viewport = $derived.by(() => {
		const canvasSizes = context.stateLayoutDerived.canvasSizes();
		const width = canvasSizes.width / mainLayout.scale;
		const height = canvasSizes.height / mainLayout.scale;
		const left = (mainLayout.width - width) / 2;
		const top = (mainLayout.height - height) / 2;

		return { width, height, left, top, right: left + width, bottom: top + height };
	});

	const mobileBar = $derived(mobile ? MOBILE_BAR[layoutType as keyof typeof MOBILE_BAR] : null);

	/** Bloc de boutons de l'UI Stake, dans SON espace de design. Desktop/tablet. */
	const barBlock = $derived.by(() => {
		const height = context.stateLayoutDerived.mainLayoutStandard().height;
		const map = {
			desktop: { size: DESKTOP_BASE_SIZE, margin: 10 },
			tablet: { size: TABLET_BASE_SIZE, margin: 30 },
			landscape: { size: LANDSCAPE_BASE_SIZE, margin: 40 },
			portrait: { size: PORTRAIT_BASE_SIZE, margin: 400 - PORTRAIT_BASE_SIZE * 0.5 },
		}[layoutType];

		return { top: height - map.size - map.margin, size: map.size };
	});

	const DESKTOP_BAR_SLOTS = ['MENU', 'BUY', 'BALANCE', 'BET', 'SPIN'];

	// Publie ce que le rendu utilise réellement — le panneau ne recalcule rien.
	$effect(() => {
		visualMetrics.viewportWidth = context.stateLayoutDerived.canvasSizes().width;
		visualMetrics.viewportHeight = context.stateLayoutDerived.canvasSizes().height;
		visualMetrics.layoutType = layoutType;
		visualMetrics.designWidth = mainLayout.width;
		visualMetrics.designHeight = mainLayout.height;
		visualMetrics.scale = mainLayout.scale;
		visualMetrics.gridWidth = BOARD_SIZES.width * mainLayout.scale;
		visualMetrics.gridHeight = BOARD_SIZES.height * mainLayout.scale;
		visualMetrics.cellSize = CELL_SIZE * mainLayout.scale;
		visualMetrics.symbolSize = SYMBOL_DISPLAY_SIZE * mainLayout.scale;
		visualMetrics.gap = CELL_GAP * mainLayout.scale;
		visualMetrics.logoBand = bands.logo * mainLayout.scale;
		visualMetrics.gameBarBand = bands.gameBar * mainLayout.scale;
		visualMetrics.spinSize = (mobileBar?.spin ?? 0) * mainLayout.scale;
	});

	// Plateau fixe de revue (§16) : rejoué via l'event Stake existant.
	let settled = false;
	$effect(() => {
		if (settled) return;
		settled = true;
		context.eventEmitter.broadcast({ type: 'boardSettle', board: VISUAL_BOARD });
	});
</script>

<MainContainer>
	{#if visualGuides.safeZones}
		<!-- Bleu : l'espace de design. Il ne remplit pas forcément le viewport. -->
		<Rectangle
			width={mainLayout.width}
			height={mainLayout.height}
			backgroundAlpha={0}
			borderColor={GUIDE.design}
			borderWidth={2}
			borderAlpha={0.9}
		/>
	{/if}

	<!-- ── Bandes réservées, ancrées aux bords du viewport ──────────────────── -->
	<Rectangle
		x={viewport.left}
		y={viewport.top}
		width={viewport.width}
		height={bands.logo}
		backgroundColor={GUIDE.band}
		backgroundAlpha={0.08}
		borderColor={GUIDE.band}
		borderWidth={1}
		borderAlpha={0.5}
	/>
	<Text
		x={viewport.left + viewport.width * 0.5}
		y={viewport.top + bands.logo * 0.5}
		anchor={{ x: 0.5, y: 0.5 }}
		text="ZONE LOGO"
		style={{ fontFamily: 'monospace', fontSize: Math.min(18, bands.logo * 0.4), fill: GUIDE.band }}
	/>

	<Rectangle
		x={viewport.left}
		y={viewport.bottom - bands.gameBar}
		width={viewport.width}
		height={bands.gameBar}
		backgroundColor={GUIDE.band}
		backgroundAlpha={0.08}
		borderColor={GUIDE.band}
		borderWidth={1}
		borderAlpha={0.5}
	/>

	<!-- ── Game bar MOBILE : gros Spin centré, Menu discret en bas à gauche ─── -->
	{#if mobileBar}
		{@const barCenterY = viewport.bottom - mobileBar.bottomMargin - mobileBar.spin * 0.5}
		<Rectangle
			anchor={{ x: 0.5, y: 0.5 }}
			x={viewport.left + viewport.width * 0.5}
			y={barCenterY}
			width={mobileBar.spin}
			height={mobileBar.spin}
			borderRadius={mobileBar.spin * 0.5}
			backgroundColor={0x0b1f18}
			backgroundAlpha={0.75}
			borderColor={GUIDE.spin}
			borderWidth={3}
		/>
		<Text
			x={viewport.left + viewport.width * 0.5}
			y={barCenterY}
			anchor={{ x: 0.5, y: 0.5 }}
			text="SPIN"
			style={{ fontFamily: 'monospace', fontSize: mobileBar.spin * 0.24, fill: GUIDE.spin }}
		/>

		<Rectangle
			anchor={{ x: 0.5, y: 0.5 }}
			x={viewport.left + mobileBar.sideMargin + mobileBar.menu * 0.5}
			y={viewport.bottom - mobileBar.bottomMargin - mobileBar.menu * 0.5}
			width={mobileBar.menu}
			height={mobileBar.menu}
			borderRadius={mobileBar.menu * 0.3}
			backgroundColor={0x000000}
			backgroundAlpha={0.5}
			borderColor={GUIDE.bar}
			borderWidth={2}
			borderAlpha={0.7}
		/>
		<Text
			x={viewport.left + mobileBar.sideMargin + mobileBar.menu * 0.5}
			y={viewport.bottom - mobileBar.bottomMargin - mobileBar.menu * 0.5}
			anchor={{ x: 0.5, y: 0.5 }}
			text="MENU"
			style={{ fontFamily: 'monospace', fontSize: mobileBar.menu * 0.2, fill: GUIDE.bar }}
		/>
	{:else}
		<Text
			x={viewport.left + viewport.width * 0.5}
			y={viewport.bottom - bands.gameBar + 16}
			anchor={{ x: 0.5, y: 0 }}
			text={`ZONE GAME BAR réservée — ${Math.round(bands.gameBar)} u`}
			style={{ fontFamily: 'monospace', fontSize: 18, fill: GUIDE.band }}
		/>
	{/if}

	{#if visualGuides.gridBounds}
		<Rectangle
			anchor={{ x: 0.5, y: 0.5 }}
			x={boardLayout.x}
			y={boardLayout.y}
			width={BOARD_SIZES.width}
			height={BOARD_SIZES.height}
			backgroundAlpha={0}
			borderColor={GUIDE.grid}
			borderWidth={2}
		/>
	{/if}

	{#if visualGuides.cellBounds || visualGuides.centers}
		<Container
			x={boardLayout.x}
			y={boardLayout.y}
			pivot={{ x: BOARD_SIZES.width / 2, y: BOARD_SIZES.height / 2 }}
		>
			{#each columns as column (column)}
				{#each rows as row (row)}
					{#if visualGuides.cellBounds}
						<!-- Le PAS de la grille, pas la case dessinée : révèle la gouttière. -->
						<Rectangle
							anchor={{ x: 0.5, y: 0.5 }}
							x={getSymbolX(column)}
							y={getSymbolY(row)}
							width={SYMBOL_SIZE}
							height={SYMBOL_SIZE}
							backgroundAlpha={0}
							borderColor={GUIDE.cell}
							borderWidth={1}
							borderAlpha={0.8}
						/>
					{/if}
					{#if visualGuides.centers}
						<Rectangle
							anchor={{ x: 0.5, y: 0.5 }}
							x={getSymbolX(column)}
							y={getSymbolY(row)}
							width={9}
							height={1}
							backgroundColor={GUIDE.center}
						/>
						<Rectangle
							anchor={{ x: 0.5, y: 0.5 }}
							x={getSymbolX(column)}
							y={getSymbolY(row)}
							width={1}
							height={9}
							backgroundColor={GUIDE.center}
						/>
					{/if}
				{/each}
			{/each}
		</Container>
	{/if}
</MainContainer>

<!-- ── Contrôle desktop/tablet : le vrai bloc de boutons Stake ─────────────── -->
{#if !mobile}
	<MainContainer standard alignVertical="bottom">
		<Container y={barBlock.top}>
			<Rectangle
				width={context.stateLayoutDerived.mainLayoutStandard().width}
				height={barBlock.size}
				backgroundColor={0x000000}
				backgroundAlpha={0.45}
				borderColor={GUIDE.bar}
				borderWidth={2}
				borderAlpha={0.8}
			/>
			{#each DESKTOP_BAR_SLOTS as slot, index (slot)}
				<Text
					x={(context.stateLayoutDerived.mainLayoutStandard().width * (index + 0.5)) /
						DESKTOP_BAR_SLOTS.length}
					y={barBlock.size * 0.5}
					anchor={{ x: 0.5, y: 0.5 }}
					text={slot}
					style={{ fontFamily: 'monospace', fontSize: barBlock.size * 0.28, fill: GUIDE.bar }}
				/>
			{/each}
		</Container>
	</MainContainer>
{/if}
