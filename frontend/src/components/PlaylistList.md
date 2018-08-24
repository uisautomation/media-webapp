### Examples

```js
let playlists = [1, 2, 3, 4, 5, 6, 7, 8].map(index => ({
    title: 'Item ' + index,
    description: 'Description of media item ' + index,
    id: '#item-' + index,
}));

<PlaylistList resources={playlists} />
```


```js
<PlaylistList isLoading />
```

### CSS API

You can override the injected class names with the ``classes`` property. This
property accepts the following keys:

* ``root``
* ``buttonRoot``
