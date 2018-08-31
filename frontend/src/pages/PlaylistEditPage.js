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
import BodySection from "../components/BodySection";
import RenderedMarkdown from '../components/RenderedMarkdown';
import Page from "../containers/Page";
import IfOwnsChannel from "../containers/IfOwnsChannel";
import Draggable from "../components/Draggable";
import _ from "lodash";

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
    };

    this.patchMediaIdsDebounced = _.debounce(this.patchMediaIdsDebounced, 1000)
  }

  /**
   * Updates the order of the playlist's mediaIds after being debounced.
   */
  patchMediaIdsDebounced(media) {
    const { match: { params: { pk } } } = this.props;
    playlistPatch({id: pk, mediaIds: media.map(({id}) => id)});
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
    const media = this.state.playlist.media.slice();
    media.splice(hoverIndex, 0, ...media.splice(dragIndex, 1));
    this.setState({ playlist: { ...this.state.playlist, media } });
    // save the new order
    this.patchMediaIdsDebounced(media);
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
 * A section of the body with a heading and a editable playlist and allows reordering of the list
 * with drag and drop.
 */
const EditableListSectionComponent = ({ classes, playlist, moveListItem }) => {
  return (
    <BodySection>
      <Grid container justify='center'>
        <Grid item xs={12} sm={10} md={8} lg={6}>
          <Typography variant='display1' className={classes.title} gutterBottom>
            {playlist.title}
          </Typography>
          <Typography variant='body1' component='div'>
            <RenderedMarkdown source={playlist.description}/>
          </Typography>
          <Typography variant='headline' gutterBottom>
            Media items
          </Typography>
          <List>
            {playlist.media.map(mediaResourceToItem).map(({url, imageUrl, title}, index) => (
              <Draggable key={ url } index={ index } moveItem={ moveListItem } >
                <ListItem className={classes.listItem}>
                  <Avatar src={imageUrl} />
                  <ListItemText primary={title} />
                  <ListItemSecondaryAction className={classes.action}>
                    <ReorderIcon/>
                  </ListItemSecondaryAction>
                </ListItem>
              </Draggable>
            ))}
          </List>
        </Grid>
      </Grid>
    </BodySection>
  )
};

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

const EditableListSection = withStyles(styles)(EditableListSectionComponent);

export default PlaylistEditPage;
