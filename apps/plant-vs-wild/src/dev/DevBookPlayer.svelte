<script lang="ts">
	/**
	 * Lecteur de book mocké — OUTIL DE DÉVELOPPEMENT UNIQUEMENT.
	 *
	 * Il ne fabrique aucun résultat : il donne un book écrit à la main au
	 * pipeline Stake normal, exactement comme le Debug Panel de `apps/lines` le
	 * fait avec un book produit par le Math.
	 *
	 * Monté uniquement sous `import.meta.env.DEV` (voir routes/+layout.svelte).
	 */
	import { playBookEvents } from '../game/utils';
	import book from '../stories/data/base_book_cascade';

	let playing = $state(false);
	let plays = $state(0);
	let lastError = $state('');

	const play = async () => {
		if (playing) return;
		playing = true;
		lastError = '';
		try {
			await playBookEvents(book.bookEvents);
			plays += 1;
		} catch (error) {
			lastError = error instanceof Error ? error.message : String(error);
		} finally {
			playing = false;
		}
	};
</script>

<aside class="book-player">
	<button onclick={play} disabled={playing}>
		{playing ? 'lecture…' : '▶ CASCADE'}
	</button>
	<span>lectures : {plays}</span>
	{#if lastError}<span class="error">{lastError}</span>{/if}
</aside>

<style>
	.book-player {
		position: fixed;
		left: 8px;
		bottom: 8px;
		z-index: 99999;
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 8px 10px;
		font: 12px/1.4 ui-monospace, Menlo, Consolas, monospace;
		color: #e7e7e7;
		background: rgba(16, 16, 20, 0.94);
		border: 1px solid #4a4a55;
		border-radius: 4px;
	}

	button {
		padding: 6px 12px;
		background: #2a2a33;
		color: #e7e7e7;
		border: 0;
		border-radius: 3px;
		cursor: pointer;
		font: inherit;
		letter-spacing: 0.08em;
	}

	button:disabled {
		opacity: 0.5;
		cursor: default;
	}

	.error {
		color: #ff6b6b;
	}
</style>
