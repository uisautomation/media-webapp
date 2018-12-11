// API which is specific to the UI
//
// The endpoints used here are not part of the API per se but are implemented by the UI for
// UI-specific tasks.

// A generic response from the UI endpoints.
export interface IResponse {
  // The body of the response parsed as JSON.
  body?: { [x: string]: any };

  // The response object itself
  response: Response;
}

export interface IMediaItemJWPConfiguration {
  id: string;

  title: string;

  description: string;

  playlistUrl: string;
}

export interface IJWPConfiguration {
  mediaItems: IMediaItemJWPConfiguration[];
}

// A response from a JWP configuration endpoint.
export interface IJWPConfigurationResponse extends IResponse {
  body?: IJWPConfiguration;
}

/**
 * A wrapper around fetch() which fetches a URL using the credentials of the currently logged in
 * user. Returns a promise which is resolved with an object of type IResponse. It is up to the
 * caller to check that the response succeeded (via, e.g., response.ok).
 */
export const uiFetch = (
  input: string | Request, init: RequestInit = {}
): Promise<any> => (
  fetch(input, {credentials: 'include', ...init})
  .then(response => Promise.all([
    Promise.resolve(response),
    response.json().catch(error => undefined),
  ]))
  .then(([response, body]) => ({response, body}))
);

/**
 * GET JWP player configuration for a media item.
 */
export const mediaItemJWPConfigurationGet = (itemId: string) => (
  uiFetch(`/media/${itemId}/jwp`) as Promise<IJWPConfigurationResponse>
);

/**
 * GET JWP player configuration for a playlist.
 */
export const playlistJWPConfigurationGet = (playlistId: string) => (
  uiFetch(`/playlists/${playlistId}/jwp`) as Promise<IJWPConfigurationResponse>
);
