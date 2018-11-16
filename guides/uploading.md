# A guide to uploading new media items to the Media Platform

This document provides a guide on using the Media Platform API to publish a
video stream.

Throughout this document we will be using ``${BASE}`` to refer to the base API
URL of the Media Platform. This will be a URL like
``https://alpha.media.cam.ac.uk/api/v1alpha1/``.

Swagger/OpenAPI documentation for the API may be retrieved via a HTTP GET to
``${BASE}/swagger.json`` or ``${BASE}/swagger.yaml``.

## Authentication

Authentication is currently via long lived tokens which are manually issued by
an administrator. Authenticate a request by including the following header,
replacing ``{token}`` with the issued token:

```
Authorization: Token {token}
```

## Creating a media item

All media items must be associated with a channel. To upload a new media item to
a channel, a user must have the appropriate permission on the channel. Each
channel has a unique ID which appears in the URL of the channel page on the
media item and which appears as the ``id`` property of resources returned from
HTTP GET requests to the ``${BASE}/channels/`` endpoint.

### Create media item resource

Perform an authenticated HTTP POST to ``${BASE}/media/`` with a JSON document as
the request body. The document should have *at a minimum* the following schema:

```js
{
  "title": "<human readable title for media item>",
  "channelId": "<id of channel>"
}
```

The response body will be a JSON document describing the new media item.

### Upload media

> An
> [example of this flow](https://github.com/uisautomation/media-webapp/blob/master/ui/frontend/src/containers/UploadForm.js#L173)
> is available in the frontend.

To upload media for a media item, you will need an upload endpoint. This is a
URL which accepts a HTTP POST with the media item source file form encoded as
the "file" field. **Uploading media via a HTTP POST to the upload URL does not
require further authentication beyond knowing the URL.**

To retrieve the upload URL, perform an authenticated HTTP POST to
``${BASE}/media/{id}/upload`` replacing ``{id}`` with the ``id`` property from
the JSON document describing the new media item. The request body may be empty.

The response will be a JSON document containing a one-time use upload URL in the
``url`` property.

## Associating a media item with a playlist

Similarly to channels, playlists all have a unique id associated with them. This
id appears in the URL of the playlist page on the media item and appears as the
``id`` property of resources returned from HTTP GET requests to the
``${BASE}/playlists/`` endpoint.

A playlists resource has ``mediaIds`` property which is a comma-separated list
of media ids for that playlist. To update the list:

1. Perform an authenticated HTTP GET request to ``${BASE}/playlists/{id}`` where
   ``{id}`` is the playlist id. The response will be a JSON document with a
   ``mediaIds`` property.
2. Append the desired media id to the comma-separated list in the ``mediaIds``
   property.
3. Perform an authenticated HTTP PATCH request to ``${BASE}/playlists/{id}``
   where ``{id}`` is the playlist id. The request body should be a JSON document
   with the following schema:

    ```js
    {
      "mediaIds": "<comma separated list of media ids>"
    }
    ```

