### Examples

```js
initialState = { playlist: { } };

<div>
    <PlaylistMetadataForm
        playlist={ state.playlist }
        onChange={ patch => setState({ playlist: { ...state.playlist, ...patch } }) }
        onSubmit={ () => alert('Submit!') }
        submitDisabled={ !state.playlist.name }
    />
    <h3>Playlist</h3>
    <div>{ JSON.stringify(state.playlist) }</div>
</div>
```

If you want to show an error state, set the errors object:

```js
const playlist = { title: "Surely you can't serious?" };
const errors = { title: ["I am serious.", "And don't call me Shirley."] };

<PlaylistMetadataForm playlist={ playlist } errors={ errors } />
```
