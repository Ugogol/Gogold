import type { EmitterEventBoard } from '../components/Board.svelte';
import type { EmitterEventTumbleBoard } from '../components/TumbleBoard.svelte';
import type { EmitterEventWildFlight } from '../components/WildFlight.svelte';

export type EmitterEventGame = EmitterEventBoard | EmitterEventTumbleBoard | EmitterEventWildFlight;
