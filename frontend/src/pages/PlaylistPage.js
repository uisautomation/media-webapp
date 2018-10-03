import React, { Component } from 'react';

import Button from '@material-ui/core/Button';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';
import EditIcon from '@material-ui/icons/Edit';
import DeleteIcon from '@material-ui/icons/Delete';

import FetchPlaylist from "../containers/FetchPlaylist";
import BodySection from '../components/BodySection';
import RenderedMarkdown from '../components/RenderedMarkdown';
import Page from "../containers/Page";
import DeletePlaylistDialog from "../containers/DeletePlaylistDialog";
import {setMessageForNextPageLoad} from "../containers/Snackbar";
import IfOwnsChannel from "../containers/IfOwnsChannel";
import MediaList from "../components/MediaList";
import {playlistDelete} from "../api";

/**
 * A list of media for a playlist. Upon mount, it fetches the playlist details and then a list of the
 * media items and shows them to the user.
 */
const PlaylistPage = ({ match: { params: { pk } } }) => (
  <Page gutterTop><FetchPlaylist id={ pk } component={ StyledPageContent } /></Page>
);

/** Playlist page content. */
class PageContent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      // Controls the visibility of the delete confirmation dialog.
      deleteDialogOpen: false,
    }
  }

  /** Handles the user's confirmation of the playlist deletion */
  handleConfirmDelete = (doDelete) => {
    this.setState({deleteDialogOpen: false});
    const { resource: playlist } = this.props;
    if (doDelete) {
      playlistDelete(playlist.id)
        .then(() => {
          setMessageForNextPageLoad(`Playlist "${playlist.title}" deleted.`);
          window.location = '/'
        })
        .catch(({ body }) => this.setState({ errors: body }));
    }
  };

  /** Gets the playlist's id. */
  getPlaylistId = () => this.props.match.params.pk;

  render() {
    const { classes, resource: playlist } = this.props;

    if (!playlist || !playlist.id) {
      return null;
    }

    return (
      <BodySection>
        <Toolbar className={classes.toolbar}>
          <Typography variant='display1' className={classes.title}>
            { playlist.title }
          </Typography>
          <IfOwnsChannel channel={playlist.channel} className={classes.buttons}>
            <Button component='a' color='primary' variant='contained'
                    href={'/playlists/' + playlist.id + '/edit'}
            >
              Edit
              <EditIcon className={classes.rightIcon}/>
            </Button>
            <Button color='primary' variant='contained'
                    onClick={() => this.setState({deleteDialogOpen: true})}>
              Delete
              <DeleteIcon className={classes.rightIcon}/>
            </Button>
          </IfOwnsChannel>
        </Toolbar>
        <RenderedMarkdown source={ playlist.description } />
        <Typography variant='headline' gutterBottom>Media items</Typography>
        <MediaList resources={playlist.mediaForUser} />
        <DeletePlaylistDialog isOpen={this.state.deleteDialogOpen} title={playlist.title}
                              handleConfirmDelete={this.handleConfirmDelete}/>
      </BodySection>
    )
  }
}

const pageContentStyles = theme => ({
  buttons: {
    '& a': {
      marginRight: theme.spacing.unit,
    },
    display: 'inline-flex',
  },
  rightIcon: {
    marginLeft: theme.spacing.unit,
  },
  title: {
    marginRight: theme.spacing.unit * 2,
  },
  toolbar: {
    paddingLeft: 0,
  },
});

const StyledPageContent = withStyles(pageContentStyles)(PageContent);

export default PlaylistPage;
