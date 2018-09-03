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
