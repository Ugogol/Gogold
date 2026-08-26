import type { EmitterEventBoard } from '../components/Board.svelte';
import type { EmitterEventTumbleBoard } from '../components/TumbleBoard.svelte';
import type { EmitterEventWildFlight } from '../components/WildFlight.svelte';
import type { EmitterEventMultiplierGrid } from '../components/MultiplierGrid.svelte';
import type { EmitterEventFreeSpinCounter } from '../components/FreeSpinCounter.svelte';
import type { EmitterEventFreeSpinBanner } from '../components/FreeSpinBanner.svelte';

export type EmitterEventGame =
	| EmitterEventBoard
	| EmitterEventTumbleBoard
	| EmitterEventWildFlight
	| EmitterEventMultiplierGrid
	| EmitterEventFreeSpinCounter
	| EmitterEventFreeSpinBanner;
