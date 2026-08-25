import type { EmitterEventBoard } from '../components/Board.svelte';
import type { EmitterEventTumbleBoard } from '../components/TumbleBoard.svelte';
import type { EmitterEventWildFlight } from '../components/WildFlight.svelte';
import type { EmitterEventMultiplierGrid } from '../components/MultiplierGrid.svelte';

export type EmitterEventGame =
	| EmitterEventBoard
	| EmitterEventTumbleBoard
	| EmitterEventWildFlight
	| EmitterEventMultiplierGrid;
