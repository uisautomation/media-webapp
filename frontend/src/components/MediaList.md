### Examples

```js
let mediaItems = [1, 2, 3, 4, 5, 6, 7, 8].map(index => ({
    title: 'Item ' + index,
    description: 'Description of media item ' + index,
    imageUrl: 'http://via.placeholder.com/640x360',
    url: '#item-' + index,
}));

<MediaList mediaItems={mediaItems} />
```


```js
<MediaList maxItemCount={4} contentLoading />
```

### CSS API

You can override the injected class names with the ``classes`` property. This
property accepts the following keys:

* ``root``
* ``buttonRoot``
