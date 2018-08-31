import React from 'react';
import {findDOMNode} from 'react-dom';
import PropTypes from 'prop-types';
import {DragSource, DropTarget} from "react-dnd/lib/index";

// https://gist.github.com/kavimaluskam/19b9bd5d3ae1142c01aee52059abac21

const cardSource = {
  beginDrag(props) {
    return {
      index: props.index,
    };
  },
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

    // Note: we're mutating the monitor item here!
    // Generally it's better to avoid mutations,
    // but it's good here for the sake of performance
    // to avoid expensive index searches.
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

/** FIXME */
const Draggable = ({ isDragging, connectDragSource, connectDropTarget, children }) => {
  const opacity = isDragging ? 0 : 1;
  return connectDragSource(
    connectDropTarget(
      <div style={{cursor: 'move', opacity}}>{ children }</div>
  ))
};

Draggable.propTypes = {
  /** FIXME */
  index: PropTypes.number.isRequired,
  /** FIXME */
  key: PropTypes.string.isRequired,
  /** FIXME */
  moveItem: PropTypes.func.isRequired,
};

export default withDropTarget(withDropSource(Draggable));
