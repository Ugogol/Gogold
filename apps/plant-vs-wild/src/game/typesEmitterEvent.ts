import type { EmitterEventBoard } from '../components/Board.svelte';
import type { EmitterEventTumbleBoard } from '../components/TumbleBoard.svelte';

export type EmitterEventGame = EmitterEventBoard | EmitterEventTumbleBoard;
