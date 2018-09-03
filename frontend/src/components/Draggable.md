A component which enables drap and drop on the component that it wraps. While react-dnd is quite
general, this component implements a special drag and drop case where the wrapped components are
both drag sources and drop targets. Note that the component must be surrounded by a
DraggableContext component for drag and drop to work. The component closely follows the
react-dnd example in https://gist.github.com/kavimaluskam/19b9bd5d3ae1142c01aee52059abac21.

#### Properties

- **index (number - required)** A sequential index that defines the position of the draggable component within the set 
  of target components.
- **moveItem (func - required)** Called with dragIndex & hoverIndex when a source item is hovering above a valid target. 
  It is responsible for updating the order of the collection.

### Examples

```js
const List = require('@material-ui/core/List').default;
const ListItem = require('@material-ui/core/ListItem').default;
const DraggableContext = require('./DraggableContext').default;

initialState = { items: [
  {id: '1', text: 'Mama pyjama rolled out of bed'}, 
  {id: '2', text: 'And ran to the police station'}, 
  {id: '3', text: 'And when Papa found, he began to shout'}, 
  {id: '4', text: 'And started the investigation'}, 
  {id: '5', text: "It's against the law"},
  {id: '6', text: 'It was against the law'},
  {id: '7', text: 'What the mama saw'},
  {id: '8', text: 'It was against the law'},
]};

const moveListItem = (dragIndex, hoverIndex) => {
  const items = state.items.slice();
  items.splice(hoverIndex, 0, ...items.splice(dragIndex, 1));
  setState({ items: items });
};

<DraggableContext>
  <List>
    {state.items.map(({id, text}, index) => (
      <Draggable key={ id } index={ index } moveItem={ moveListItem }>
        <ListItem style={{backgroundColor: '#eeeeee'}}>{ text }</ListItem>
      </Draggable>
    ))}
  </List>
</DraggableContext>
```
