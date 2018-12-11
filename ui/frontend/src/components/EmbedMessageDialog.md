### Examples

```js
<div style={{ backgroundColor: 'black', padding: 16 }}>
  <EmbedMessageDialog
    title="Some title"
    message="Something went wrong."
    technicalDescription="The frobnicators were degaussed incorrectly."
  />
</div>
```

```js
<div style={{ backgroundColor: 'black', padding: 16 }}>
  <EmbedMessageDialog
    title="Some title"
    message="Something went wrong."
    technicalDescription="The frobnicators were degaussed incorrectly."
    showSignIn={ false }
  />
</div>
```

### CSS API

You can override the injected class names with the ``classes`` property. This
property accepts the following keys:

* ``root``
