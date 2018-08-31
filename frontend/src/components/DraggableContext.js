import React from 'react';
import HTML5Backend from "react-dnd-html5-backend/lib/index";
import {DragDropContext} from "react-dnd/lib/index";

/** This component exists purely to be able to implement the example in Draggable.md.
 * TODO this is far from ideal
 */

const DraggableContext = DragDropContext(HTML5Backend)(({ children }) => (
  <div>{ children }</div>
));

export default DraggableContext;
