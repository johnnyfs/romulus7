/**
 * Event API types.
 *
 * ABSTRACTION BOUNDARY: This is the ONLY file that knows the event
 * endpoint URL and response shape.
 */

export type EventCallback = {
  execution_id?: string;
  execution_name?: string;
  execution_color?: string;
  [key: string]: unknown;
};

export type EventPayload = {
  kind: "command.stdout";
  line: string;
  callback?: EventCallback | null;
};

export type Event = {
  id: number;
  created_at: string;
  source_type: "dispatch";
  source_id: string;
  type: "command.stdout";
  payload: EventPayload;
};

export const EVENTS_STREAM_URL = "/api/v1/events/stream";
