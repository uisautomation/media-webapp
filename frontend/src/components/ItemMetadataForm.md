### Examples

```js
const { Component } = require('react');

const languageOptions = [
  {value: '', label: ''},
  {value: 'hye', label: 'Armenian'},
  {value: 'bty', label: 'Bobot'},
  {value: 'swc', label: 'Congo Swahili'},
  {value: 'doq', label: 'Dominican Sign Language'},
  {value: 'acp', label: 'Eastern Acipa'},
  {value: 'fra', label: 'French'},
];


class RenderedForm extends Component {
  constructor(props) {
    super(props);
    this.state = { item: { } };
  }

  render() {
    const { item } = this.state;
    return <div>
      <h3>Form</h3>
      <ItemMetadataForm
        item={ item }
        onChange={ patch => this.handlePatch(patch) }
        onSubmit={ () => alert('Submit!') }
        submitDisabled={ !item.name }
        languageOptions={ languageOptions }
      />
      <h3>Item</h3>
      <div>{ JSON.stringify(item) }</div>
    </div>;
  }

  handlePatch(patch) {
    const { item } = this.state;
    this.setState({ item: { ...item, ...patch } });
  }
}

<RenderedForm />
```

If you want to show an error state, set the errors object:

```js
const item = { 
  title: 'The Dead Parrot Sketch', 
  description: 'Oh what a lovely description!', 
  copyright: 'Mike Bamford PLC'
};
const errors = { 
  title: ['The parrot is alive.', 'It is sleeping.'],
  description: ['Not really a description.', 'A bit too meta.'],
  publishedAt: ['This is a fake date.', 'Fake fake date!'],
  copyright: ['Not a proper copyright.', 'You are being silly.'],
};

<ItemMetadataForm item={ item } errors={ errors } />
```
