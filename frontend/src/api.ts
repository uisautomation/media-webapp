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

// The base URL for the SMS application - used to create legacy URLs.
export const BASE_SMS_URL = 'https://sms.cam.ac.uk';

// Get Django's CSRF token from the page from the first element named "csrfmiddlewaretoken". If no
// such element is present, the token is empty.
const CSRF_ELEMENT =
  (document.getElementsByName('csrfmiddlewaretoken')[0] as HTMLInputElement);
const CSRF_TOKEN = (typeof(CSRF_ELEMENT) !== 'undefined') ? CSRF_ELEMENT.value : '';

// Headers to send with fetch request which authorises us to Django.
const API_HEADERS = {
  'Content-Type': 'application/json',
  'X-CSRFToken': CSRF_TOKEN,
};

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

/** A media download source. */
export interface ISource {
  mime_type: string;
  url: string;
  width?: number;
  height?: number;
}

/** A media resource. */
export interface IMediaResource {
  id: string;
  title: string;
  description: string;
  published_at_timestamp: number;
  poster_image_url?: string;
  duration: number;
  player_url: string;
  source?: ISource[];
  media_id: number;
};

/** A collection resource. */
export interface ICollectionResource {
  id: string;
  title: string;
  description: string;
  poster_image_url?: string;
  collection_id: number;
};

/** A media list response. */
export interface IMediaListResponse {
  results: IMediaResource[];
  limit: number;
  offset: number;
  total: number;
};

/** A collection list response. */
export interface ICollectionListResponse {
  results: ICollectionResource[];
  limit: number;
  offset: number;
  total: number;
};

/** A query to the media list endpoint. */
export interface IMediaQuery {
  search?: string;
  ordering?: string;
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
  input: string | Request, init: RequestInit = {}
): Promise<any | IError> => (
  fetch(input, {
    credentials: 'include',
    ...init,
    headers: {
      ...API_HEADERS,
      ...init.headers,
    }
  })
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
  })
);

/** List media resources. */
export const mediaList = (
  { search, ordering }: IMediaQuery = {}
): Promise<IMediaListResponse | IError> => {
  return apiFetch(API_ENDPOINTS.mediaList + objectToQueryPart({ search, ordering }));
};

/** List collection resources. */
export const collectionList = (
  { search, ordering }: IMediaQuery = {}
): Promise<ICollectionListResponse | IError> => {
  return apiFetch(API_ENDPOINTS.collectionList + objectToQueryPart({ search, ordering }));
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
  { collection_id, title, description, poster_image_url }: ICollectionResource
) => ({
  description,
  imageUrl: poster_image_url || CollectionDefaultImage,
  label: 'Collection',
  title,
  url: BASE_SMS_URL + '/collection/' + collection_id,
});

/**
 * A function which maps an API media resource to a media item for use by, e.g., MediaItemCard.
 */
export const mediaResourceToItem = (
  { id, title, description, poster_image_url }: IMediaResource
) => ({
  description,
  imageUrl: poster_image_url,
  title,
  url: '/media/' + id,
});
