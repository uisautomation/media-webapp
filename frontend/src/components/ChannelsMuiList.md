## Examples

In basic use, the channel list shows an avatar and name for each channel:

```js
const channels = require('./ChannelsMuiList').mockChannels;
<ChannelsMuiList channels={channels} />
```

If the width of the list is constrained, channel names are truncated:

```js
const channels = require('./ChannelsMuiList').mockChannels;
<div style={{ border: '1px solid red', width: '260px' }}>
    <ChannelsMuiList channels={channels} />
</div>
```

The ``trimCount`` prop can be used to collapse the list to show a subset of
channels.

```js
const channels = require('./ChannelsMuiList').mockChannels;
<ChannelsMuiList channels={channels} trimCount={3} />
```

If the ``trimCount`` prop is bigger or equal to the number of channels, the
control is not displayed.

```js
const channels = require('./ChannelsMuiList').mockChannels;
<ChannelsMuiList channels={channels} trimCount={channels.length} />
```
