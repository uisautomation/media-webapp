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


import { playlistPatch, mediaResourceToItem } from '../api';
import FetchPlaylist from "../containers/FetchPlaylist";
import BodySection from "../components/BodySection";
import RenderedMarkdown from '../components/RenderedMarkdown';
import Page from "../containers/Page";
import IfOwnsChannel from "../containers/IfOwnsChannel";
import Draggable from "../components/Draggable";
import _ from "lodash";

/**
 * A editable list of media for a playlist. Upon mount, it fetches the playlist with a list of the
 * media items and shows them to the user. At the moment the list can only be re-ordered by drag/drop.
 * The page is split into two components: page and content so that FetchPlaylist can be used
 */

const PlaylistEditPage = ({ match: { params: { pk } } }) => (
  <Page gutterTop>
    <FetchPlaylist id={ pk } component={ PlaylistEditPageContent } />
  </Page>
);

const PlaylistEditPageContent = ({ resource: playlist }) => (
  playlist
  ?
  <div>
    <IfOwnsChannel channel={playlist.channel}>
      <BodySection>
        <Grid container justify='center'>
          <Grid item xs={12} sm={10} md={8} lg={6}>
            <Typography variant='display1' gutterBottom>
              {playlist.title}
            </Typography>
            <Typography variant='body1' component='div'>
              <RenderedMarkdown source={playlist.description}/>
            </Typography>
            <Typography variant='headline' gutterBottom>
              Media items
            </Typography>
            <StyledReorderablePlaylistList playlist={playlist}/>
          </Grid>
        </Grid>
      </BodySection>
    </IfOwnsChannel>
    <IfOwnsChannel channel={playlist.channel} hide>
      <Typography variant="headline" component="div">
        You cannot edit this playlist.
      </Typography>
    </IfOwnsChannel>
  </div>
  :
  null
);

/**
 * Displays a list of playlist items that can be reordered by dragging and dropping.
 */

class ReorderablePlaylistList extends Component {

  constructor(props) {
    super(props);

    this.state = {
      // The playlist resource
      media: this.props.playlist.media.slice(),
    };
  }

  /**
   * Updates the order of the playlist's mediaIds after being debounced.
   */
  patchMediaIdsDebounced = _.debounce((media) => {
    const { playlist: { id: pk } } = this.props;
    playlistPatch({id: pk, mediaIds: media.map(({id}) => id)});
  }, 800);

  /**
   * Handles the moveItem Draggable event - moves an item to the new position in the list.
   */
  handleMoveItem = (dragIndex, hoverIndex) => {
    const media = this.state.media.slice();
    media.splice(hoverIndex, 0, ...media.splice(dragIndex, 1));
    this.setState({media: media});
    // save the new order
    this.patchMediaIdsDebounced(media);
  };

  render() {
    const { classes } = this.props;
    const { media } = this.state;
    return (
      <List>
        {media.map(mediaResourceToItem).map(({url, imageUrl, title}, index) => (
          <Draggable key={url} index={index} moveItem={this.handleMoveItem}>
            <ListItem className={classes.listItem}>
              <Avatar src={imageUrl}/>
              <ListItemText primary={title}/>
              <ListItemSecondaryAction className={classes.action}>
                <ReorderIcon/>
              </ListItemSecondaryAction>
            </ListItem>
          </Draggable>
        ))}
      </List>
    )
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

const StyledReorderablePlaylistList = withStyles(styles)(ReorderablePlaylistList);

export default PlaylistEditPage;
