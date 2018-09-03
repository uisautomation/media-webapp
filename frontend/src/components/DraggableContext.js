import React from 'react';
import {DragDropContext} from "react-dnd/lib/index";
import HTML5Backend from "react-dnd-html5-backend/lib/index";
import TouchBackend from "react-dnd-touch-backend";

/**
 * Provides a DragDropContext for the Draggable component. Decides whether or not the agent is a
 * mobile device.
 */

// use the touch backend if the agent supports touch events
const BACKEND = 'ontouchstart' in document.documentElement ? TouchBackend : HTML5Backend;

const DraggableContext = DragDropContext(BACKEND)(({ children }) => (
  <div>{ children }</div>
));

export default DraggableContext;
