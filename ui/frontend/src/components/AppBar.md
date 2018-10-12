### Examples

```js
const Button = require('@material-ui/core/Button').default;

<AppBar autoFocus={false} onSearch={q => alert('Your search: ' + q)}>
  <Button variant="raised" color="secondary">Sign in</Button>
</AppBar>
```

### CSS API

You can override the injected class names with the ``classes`` property. This
property accepts the following keys:

* ``root``
* ``searchFormRoot``
* ``searchFormButtonRoot``
* ``searchFormInputRoot``
