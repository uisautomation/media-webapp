### Examples

```js
let channels = [1, 2, 3, 4, 5, 6, 7, 8].map(index => ({
    title: 'Item ' + index,
    description: 'Description of media item ' + index,
    id: '#item-' + index,
}));

<ChannelList resources={channels} />
```


```js
<ChannelList isLoading />
```

### CSS API

You can override the injected class names with the ``classes`` property. This
property accepts the following keys:

* ``root``
* ``buttonRoot``
