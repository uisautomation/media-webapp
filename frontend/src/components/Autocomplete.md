### Examples

```js
cats = [
  {value: 'A', label: 'African Golden Cat'},
  {value: 'B', label: 'Black-footed Cat'},
  {value: 'C', label: 'Caracal'},
  {value: 'E', label: 'Eurasian Lynx'},
  {value: 'F', label: 'Fishing Cat'},
  {value: 'G', label: 'Geoffroy’s Cat'},
  {value: 'I', label: 'Iberian Lynx'},
  {value: 'J', label: 'Jaguarundi'},
  {value: 'K', label: 'Kodkod'},
  {value: 'M', label: 'Margay'},
  {value: 'O', label: 'Ocelot'},
  {value: 'P', label: "Pallas' Cat"},
  {value: 'R', label: 'Rusty-spotted Cat'},
  {value: 'S', label: 'Serval'},
  {value: 'W', label: 'Wildcat'},
];

initialState = { selection: null };

<div>
    <Autocomplete
        options={ cats }
        label='Small Wild Cats'
        onChange={ selection => setState({ selection }) }
        defaultValue='P'
    />
    <h3>Selection</h3>
    <div>{ JSON.stringify(state.selection) }</div>
</div>
```
