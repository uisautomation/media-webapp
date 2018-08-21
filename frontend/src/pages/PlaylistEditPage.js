import React, { Component } from 'react';

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
import RenderedMarkdown from '../components/RenderedMarkdown';
import Page from "../containers/Page";
import RequiresEdit from "../containers/RequiresEdit";

/**
 * A editable list of media for a playlist. Upon mount, it fetches the playlist with a list of the
 * media items and shows them to the user. The list can be re-ordered by drag/drop.
 */
class PlaylistEditPage extends Component {
  constructor(props) {
    super(props);

    this.state = {
      // The playlist resource
      playlist: { id: '', items: [] },

      // The index of the items being dragged.
      dragStart: null,
    }
  }

  componentWillMount() {
    // As soon as the index page mounts, fetch the playlist.
    const { match: { params: { pk } } } = this.props;
    playlistGet(pk)
      .then(playlist => {
        this.setState({ playlist });
      });
  }

  /**
   * Function called when an item drag begins. Saves the index of the dragged item.
   */
  handleDragStart(index) {
    this.setState({ dragStart: index })
  }

  /**
   * Function called when an item is dropped on another item. Reorder the list so that the target
   * item is dropped in place and the other items are shifted in the direction of the source item.
   */
  handleDrop(index) {
    const items = this.state.playlist.items.slice();
    const mediaItem = items.splice(this.state.dragStart, 1);
    items.splice(index, 0, ...mediaItem);
    this.setState({ playlist: { ...this.state.playlist, items } });
    // save the new order
    const { match: { params: { pk } } } = this.props;
    playlistPatch({id: pk, mediaIds: items.map(({id}) => id)});
  }

  render() {
    const { playlist } = this.state;
    return (
      <Page>
      {
        playlist !== null
        ?
        <RequiresEdit channel={playlist.channel} displayOnFalse="You cannot edit this playlist.">
          <EditableListSection
            handleDragStart={(index) => this.handleDragStart(index)}
            handleDrop={(index) => this.handleDrop(index)}
            playlist={playlist}
          />
        </RequiresEdit>
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
      classes, handleDragStart, handleDrop, playlist: {title, description, items}
    } = this.props;
    return (
      <section className={classes.section}>
        <Grid container justify='center'>
          <Grid item xs={12} sm={10} md={8} lg={6}>
            <Typography variant='display1' gutterBottom>
              {title}
            </Typography>
            <Typography variant='body1' component='div'>
              <RenderedMarkdown source={description}/>
            </Typography>
            <Typography variant='headline' gutterBottom>
              Media items
            </Typography>
            <List>
              {items.map(mediaResourceToItem).map((item, index) => (
                <div key={index} ref={'item-' + index}
                     onDragOver={event => event.preventDefault()}
                     onDrop={() => handleDrop(index)}
                >
                  <ListItem button className={classes.listItem}>
                    <Avatar src={item.imageUrl}/>
                    <ListItemText primary={item.title}/>
                    <ListItemSecondaryAction className={classes.action}>
                      <div
                        draggable={true}
                        onDragStart={event => {
                          handleDragStart(index);
                          // Displays the ghost item correctly
                          const ghost = this.refs['item-' + index];
                          const x = ghost.clientWidth - 20;
                          const y = ghost.clientHeight / 2;
                          event.dataTransfer.setDragImage(ghost, x, y);
                        }}
                      >
                        <ReorderIcon/>
                      </div>
                    </ListItemSecondaryAction>
                  </ListItem>
                </div>
              ))}
            </List>
          </Grid>
        </Grid>
      </section>
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
  section: {
    marginTop: theme.spacing.unit * 2
  },
});

const EditableListSection = withStyles(styles)(EditableListSectionComponent);

export default PlaylistEditPage;
