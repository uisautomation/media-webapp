### Examples

```js
let mediaItems = [1, 2, 3, 4, 5, 6, 7, 8].map(index => ({
    title: 'Item ' + index,
    description: 'Description of media item ' + index,
    posterImageUrl: 'http://via.placeholder.com/640x360',
    id: '#item-' + index,
}));

<MediaList resources={mediaItems} />
```


```js
<MediaList isLoading />
```

### CSS API

You can override the injected class names with the ``classes`` property. This
property accepts the following keys:

* ``root``
* ``buttonRoot``
