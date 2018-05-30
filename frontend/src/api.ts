/**
 * Support for interacting with the webapp's API.
 *
 * See the Django-side code under api/ for the implementation of this API.
 *
 * Note: this is the only non-trivial bit of TypeScript in the project at the moment because it is
 * useful to document the various types which these functions can return. It also provides a
 * "safe-space" to experiment with TypeScript :).
 */
import CollectionDefaultImage from './img/collection-default-image.jpg';

/**
 * When API calls fail, the related Promise is reject()-ed with an object implementing this
 * interface.
 */
export interface IError {
  /** A descriptive error. */
  error: Error,

  /** The response from the API, if any. */
  response?: Response,
};

/** A media resource. */
export interface IMediaResource {
  ui_url: string;
  title: string;
  description: string;
  poster_image_url?: string;
};

/** A collection resource. */
export interface ICollectionResource {
  ui_url: string;
  title: string;
  description: string;
  poster_image_url?: string;
};

/** A media list response. */
export interface IMediaListResponse {
  results: IMediaResource[];
};

/** A collection list response. */
export interface ICollectionListResponse {
  results: ICollectionResource[];
};

/** A query to the media list endpoint. */
export interface IMediaQuery {
  search?: string;
};

/** A query to the collection list endpoint. */
export interface ICollectionQuery {
  search?: string;
};

/** A profile response. */
export interface IProfileResponse {
  is_anonymous: boolean;
  username?: string;
  urls: {
    login: string;
  };
};

/** The various API endpoints */
export const API_ENDPOINTS = {
  collectionList: '/api/collections/',
  mediaList: '/api/media/',
  profile: '/api/profile',
};

/**
 * A wrapper around fetch() which performs an API request. Returns a Promise which is resolved with
 * the decoded JSON body of the response or which is rejected with an object implementing IError.
 *
 * Any errors are *always* logged via console.error().
 */
export const apiFetch = (
  input: string | Request, init: object = {}
): Promise<any | IError> => fetch(input, { credentials: 'include', ...init })
  .then(response => {
    if(!response || !response.ok) {
      // Always log any API errors we get.
      // tslint:disable-next-line:no-console
      console.error('API error response:', response);

      // Reject the call passing the response.
      return Promise.reject({
        error: new Error('API request returned error response'), response
      });
    }

    // Parse response body as JSON
    return response.json();
  })
  .catch(error => {
    // Always log any API errors we get.
    // tslint:disable-next-line:no-console
    console.error('API fetch error:', error);

    // Chain to the next error handler
    return Promise.reject({ error });
  });

/** List media resources. */
export const mediaList = (
  { search }: IMediaQuery = {}
): Promise<IMediaListResponse | IError> => {
  return apiFetch(API_ENDPOINTS.mediaList + objectToQueryPart({ search }));
};

/** List collection resources. */
export const collectionList = (
  { search }: IMediaQuery = {}
): Promise<ICollectionListResponse | IError> => {
  return apiFetch(API_ENDPOINTS.collectionList + objectToQueryPart({ search }));
};

/** Fetch the user's profile. */
export const profileGet= (): Promise<IProfileResponse | IError> => {
  return apiFetch(API_ENDPOINTS.profile);
}

/**
 * Convert an object with properties into a URL query string including initial '?'. If an empty
 * object is provided, the empty string is returned.
 */
const objectToQueryPart = (o: object = {}): string => {
  const urlParams = new URLSearchParams();
  Object.keys(o).forEach(key => { if(o[key] !== undefined) { urlParams.append(key, o[key]); } });
  const urlParamsString = urlParams.toString();
  return (urlParamsString === '') ? '' : '?' + urlParamsString;
};

/**
 * A function which maps an API collection resource to a media item for use by, e.g.,
 * MediaItemCard. If the collection has no associated image, a default one is substituted.
 */
export const collectionResourceToItem = (
  { ui_url, title, description, poster_image_url }: ICollectionResource
) => ({
  description,
  imageUrl: poster_image_url || CollectionDefaultImage,
  label: 'Collection',
  title,
  url: ui_url,
});

/**
 * A function which maps an API media resource to a media item for use by, e.g., MediaItemCard.
 */
export const mediaResourceToItem = (
  { ui_url, title, description, poster_image_url }: IMediaResource
) => ({
  description,
  imageUrl: poster_image_url,
  title,
  url: ui_url,
});
