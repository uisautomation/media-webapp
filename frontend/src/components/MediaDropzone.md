### Examples

Basic usage:

```js
<MediaDropzone
    onDropAccepted={files => alert(`File ${files[0].name} was selected`)}
/>
```

Disabled:

```js
<MediaDropzone
    disabled
    onDropAccepted={files => alert(`File ${files[0].name} was selected`)}
/>
```
