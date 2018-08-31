import React, { Component } from 'react';
import {findDOMNode} from 'react-dom';
import update from 'immutability-helper';

import Avatar from '@material-ui/core/Avatar';
import Grid from '@material-ui/core/Grid';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemSecondaryAction from '@material-ui/core/ListItemSecondaryAction';
import ListItemText from '@material-ui/core/ListItemText';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';
import ReorderIcon from '@material-ui/icons/Reorder';


import { playlistGet, playlistPatch, mediaResourceToItem } from '../api';
import BodySection from "../components/BodySection";
import RenderedMarkdown from '../components/RenderedMarkdown';
import Page from "../containers/Page";
import IfOwnsChannel from "../containers/IfOwnsChannel";
import {DragDropContext, DragSource, DropTarget} from "react-dnd";
import HTML5Backend from 'react-dnd-html5-backend';
import TouchBackend from 'react-dnd-touch-backend';

/**
 * A editable list of media for a playlist. Upon mount, it fetches the playlist with a list of the
 * media items and shows them to the user. The list can be re-ordered by drag/drop.
 */
class PlaylistEditPage extends Component {
  constructor(props) {
    super(props);

    this.state = {
      // The playlist resource
      playlist: { id: '', media: [] },
    }
  }

  componentWillMount() {
    // As soon as the index page mounts, fetch the playlist.
    const { match: { params: { pk } } } = this.props;
    // FIXME use FetchPlaylist
    playlistGet(pk)
      .then(playlist => {
        this.setState({ playlist });
      });
  }

  moveListItem = (dragIndex, hoverIndex) => {
    const dragitem = this.state.playlist.media[dragIndex];
    // FIXME remove dependency on immutability-helper
    this.setState(
      update(this.state, {
        playlist: {
          media: {
            $splice: [[dragIndex, 1], [hoverIndex, 0, dragitem]],
          },
        },
      }),
    );
    // FIXME de-bounce playlistPatch
  };

  render() {
    const { playlist } = this.state;
    return (
      <Page>
      {
        playlist.id !== ''
        ?
        <div>
          <IfOwnsChannel channel={playlist.channel}>
            <EditableListSection
              moveListItem={this.moveListItem}
              playlist={playlist}
            />
          </IfOwnsChannel>
          <IfOwnsChannel channel={playlist.channel} hide>
            <Typography variant="headline" component="div">
              You cannot edit this playlist.
            </Typography>
          </IfOwnsChannel>
        </div>
        :
        null
      }
      </Page>
    );
  }
}

/**
 * A section of the body with a heading and a editable playlist and allows reordering of the list.
 * The component can't be a Stateless Function because of the use of references. The drag/drop
 * stuff should be abstracted at some point but I would like the page to bed down a little so we
 * can see how best to do it.
 */
class EditableListSectionComponent extends Component {
  render() {
    const {
      classes, playlist: {title, description, media}, moveListItem
    } = this.props;
    return (
      <BodySection>
        <Grid container justify='center'>
          <Grid item xs={12} sm={10} md={8} lg={6}>
            <Typography variant='display1' className={classes.title} gutterBottom>
              {title}
            </Typography>
            <Typography variant='body1' component='div'>
              <RenderedMarkdown source={description}/>
            </Typography>
            <Typography variant='headline' gutterBottom>
              Media items
            </Typography>
            <List>
              {media.map(mediaResourceToItem).map((item, index) => (
                <PlaylistItem
                  key={ item.url }
                  index={ index }
                  item={ item }
                  moveListItem={ moveListItem }
                />
              ))}
            </List>
          </Grid>
        </Grid>
      </BodySection>
    );
  }
}

const cardSource = {
  beginDrag(props) {
    return {
      index: props.index,
    };
  },
};

const LIST_ITEM = 'listItem';

const withDropSource = DragSource(LIST_ITEM, cardSource, (connect, monitor) => ({
  connectDragSource: connect.dragSource(),
  isDragging: monitor.isDragging(),
}));

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
    props.moveListItem(dragIndex, hoverIndex);

    // Note: we're mutating the monitor item here!
    // Generally it's better to avoid mutations,
    // but it's good here for the sake of performance
    // to avoid expensive index searches.
    monitor.getItem().index = hoverIndex;
  },
};

const withDropTarget = DropTarget(LIST_ITEM, cardTarget, connect => ({
  connectDropTarget: connect.dropTarget(),
}));

class DraggableListItem extends Component {
  render() {
    const { classes, item: {imageUrl, title}, isDragging, connectDragSource, connectDropTarget } = this.props;
    const opacity = isDragging ? 0 : 1;
    return connectDragSource(
      connectDropTarget(
        <div style={{cursor: 'move', opacity}}>
          <ListItem className={classes.listItem}>
            <Avatar src={imageUrl}/>
            <ListItemText primary={title}/>
            <ListItemSecondaryAction className={classes.action}>
              <ReorderIcon/>
            </ListItemSecondaryAction>
          </ListItem>
        </div>
      )
    );
  }
}


const styles = theme => ({
  action: {
    marginRight: theme.spacing.unit
  },
  listItem: {
    backgroundColor: theme.palette.background.paper,
  },
  title: {
    marginTop: theme.spacing.unit * 2
  },
});

const PlaylistItem = withStyles(styles)(withDropTarget(withDropSource(DraggableListItem)));

const BACKEND = 'ontouchstart' in document.documentElement ? TouchBackend : HTML5Backend;

const EditableListSection = withStyles(styles)(DragDropContext(BACKEND)(EditableListSectionComponent));

export default PlaylistEditPage;
