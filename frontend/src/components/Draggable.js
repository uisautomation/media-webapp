import React from 'react';
import {findDOMNode} from 'react-dom';
import PropTypes from 'prop-types';
import {DragSource, DropTarget} from "react-dnd/lib/index";

const cardSource = {
  beginDrag: (props) => ({
      index: props.index,
  })
};

const cardTarget = {
  hover(props, monitor, component) {
    const dragIndex = monitor.getItem().index;
    const hoverIndex = props.index;

    // Don't replace items with themselves
    if (dragIndex === hoverIndex) {
      return;
    }

    // Determine rectangle on screen
    const hoverBoundingRect = findDOMNode(component).getBoundingClientRect();

    // Get vertical middle
    const hoverMiddleY = (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;

    // Determine mouse position
    const clientOffset = monitor.getClientOffset();

    // Get pixels to the top
    const hoverClientY = clientOffset.y - hoverBoundingRect.top;

    // Only perform the move when the mouse has crossed half of the items height
    // When dragging downwards, only move when the cursor is below 50%
    // When dragging upwards, only move when the cursor is above 50%

    // Dragging downwards
    if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
      return;
    }

    // Dragging upwards
    if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
      return;
    }

    // Time to actually perform the action
    props.moveItem(dragIndex, hoverIndex);

    // update the monitor with the new index
    monitor.getItem().index = hoverIndex;
  },
};

const DRAGGABLE = 'draggable';

const withDropSource = DragSource(DRAGGABLE, cardSource, (connect, monitor) => ({
  connectDragSource: connect.dragSource(),
  isDragging: monitor.isDragging(),
}));

const withDropTarget = DropTarget(DRAGGABLE, cardTarget, connect => ({
  connectDropTarget: connect.dropTarget(),
}));

/**
 * A component which enables drap and drop on the component that it wraps. While react-dnd is quite
 * general, this component implements a special drag and drop case where the wrapped components are
 * both drag sources and drop targets. Note that the component must be surrounded by a
 * DraggableContext component for drag and drop to work. The component closely follows the
 * react-dnd example in https://gist.github.com/kavimaluskam/19b9bd5d3ae1142c01aee52059abac21.
 *
 * TODO note that styleguidist isn't picking up this description so it has been copied to
 * Draggable.md manually.
 */
const Draggable = ({ isDragging, connectDragSource, connectDropTarget, children }) => {
  const opacity = isDragging ? 0 : 1;
  return connectDragSource(
    connectDropTarget(
      <div style={{cursor: 'move', opacity}}>{ children }</div>
  ))
};

Draggable.propTypes = {
  /**
   * A sequential index that defines the position of the draggable component within the set of
   * target components.
   */
  index: PropTypes.number.isRequired,
  /**
   * Called with dragIndex & hoverIndex when a source item is hovering above a valid target. It is
   * responsible for updating the order of the collection.
   */
  moveItem: PropTypes.func.isRequired,
};

export default withDropTarget(withDropSource((Draggable)));
