### Examples

```js
const { Component } = require('react');

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
