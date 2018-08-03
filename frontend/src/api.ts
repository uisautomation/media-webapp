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

// Iterate over all resources which have been embedded in the page and build a map keyed by
// resource id.
const RESOURCES_FROM_PAGE = new Map(
  Array.from(document.getElementsByTagName('script'))
  .filter((element: HTMLScriptElement) => element.type === 'application/resource+json')
  .map((element: HTMLScriptElement) => JSON.parse(element.text))
  .filter(({ id }) => !!id)
  .map((resource): [string, any] => [resource.id, resource])
);

/**
 * A function which retrieves a resource from the page by id. Note that, to avoid caching problems,
 * once retrieved, the resource is then removed from the RESOURCES_FROM_PAGE object.
 */
const resourceFromPageById = (id: string) => {
  const resource = RESOURCES_FROM_PAGE.get(id);
  if(resource) { RESOURCES_FROM_PAGE.delete(id); }
  return resource;
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
export interface IMediaSource {
  mimeType: string;
  url: string;
  width?: number;
  height?: number;
}

export interface IMediaLinks {
  legacyStatisticsUrl: string;
}

/** A media resource. */
export interface IMediaCreateResource {
  title: string;
  description: string;
  language: string;
  copyright: string;
  tags: string[];
}

/** A media resource. */
export interface IMediaResource {
  url?: string;
  id?: string;
  title: string;
  description: string;
  duration: number;
  type: string;
  publishedAt: string;
  updatedAt: string;
  createdAt: string;
  language: string;
  copyright: string;
  tags: string[];
  posterImageUrl: string;
  sources?: IMediaSource[];
  links?: IMediaLinks;
};

/** A media upload resource. */
export interface IMediaUploadResource {
  url: string;
  expires_at: string;
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

/** Create a new media resource. */
export const mediaCreate = (body: IMediaCreateResource) : Promise<IMediaResource | IError> => {
  return apiFetch(API_ENDPOINTS.mediaList, {
    body: JSON.stringify(body),
    method: 'POST',
  });
};

/** Retrieve a media resource. */
export const mediaGet = (id: string) : Promise<IMediaListResponse | IError> => {
  const resource = resourceFromPageById(id);
  if (resource) { return Promise.resolve(resource); }
  return apiFetch(API_ENDPOINTS.mediaList + id);
};

/** Patch an existing media resource. */
export const mediaPatch = (item: IMediaResource) : Promise<IMediaResource | IError> => {
  return apiFetch(API_ENDPOINTS.mediaList + item.id, {
    body: JSON.stringify(item),
    method: 'PATCH',
  });
};

/** Create a new media resource. */
export const mediaUploadGet = (item: IMediaResource) : Promise<IMediaUploadResource | IError> => {
  // TODO: decide if we want to use the URL in @id rather than key here,
  return apiFetch(API_ENDPOINTS.mediaList + item.id + '/upload');
};

/** List collection resources. */
export const collectionList = (
  { search, ordering }: IMediaQuery = {}
): Promise<ICollectionListResponse | IError> => {
  return apiFetch(API_ENDPOINTS.collectionList + objectToQueryPart({ search, ordering }));
};

/** Fetch the user's profile. */
export const profileGet = (): Promise<IProfileResponse | IError> => {
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
  { id, title, description, posterImageUrl }: IMediaResource
) => ({
  description,
  imageUrl: posterImageUrl,
  title,
  url: '/media/' + id,
});
