import React from 'react';
import {DragDropContext} from "react-dnd/lib/index";
import HTML5Backend from "react-dnd-html5-backend/lib/index";
import TouchBackend from "react-dnd-touch-backend";

/**
 * This component provides a context to all `<Draggable/>` components that it contains and is
 * essential to their correct functioning.
 */
const DraggableContext = ({ children }) => (
  <div>{ children }</div>
);

// use the touch backend if the agent supports touch events
const BACKEND = 'ontouchstart' in document.documentElement ? TouchBackend : HTML5Backend;

export default DragDropContext(BACKEND)(DraggableContext)
