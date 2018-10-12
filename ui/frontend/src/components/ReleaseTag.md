### Examples

```js
Typography = require('@material-ui/core/Typography').default;

<Typography variant="subheading">
  <ReleaseTag>Alpha</ReleaseTag>
</Typography>
```

```js
Typography = require('@material-ui/core/Typography').default;

<Typography variant="subheading" color="primary">
  <ReleaseTag color="primary">Alpha</ReleaseTag>
</Typography>
```

### CSS API

You can override the injected class names with the ``classes`` property. This
property accepts the following keys:

* ``root``
* ``colorPrimary``
* ``colorSecondary``
* ``colorDefault``
