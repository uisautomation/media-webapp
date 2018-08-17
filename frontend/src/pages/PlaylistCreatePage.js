import React, { Component } from 'react';

import Button from '@material-ui/core/Button';
import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';

import { withStyles } from '@material-ui/core/styles';

import Page from '../containers/Page';
import ChannelSelect from '../containers/ChannelSelect';
import ItemMetadataForm from "../components/ItemMetadataForm";
import {withProfile} from "../providers/ProfileProvider";
import {playlistCreate} from "../api";
import {setMessageForNextPageLoad} from "../containers/Snackbar";

/**
 * A page which allows the user to create a new playlist.
 */
class PlaylistCreatePageContents extends Component {
  constructor() {
    super();

    this.state = {
      // An error object as returned by the API or the empty object if there are no errors.
      errors: {},
      // The playlist being created.
      playlist: {},
    };
  }

  /**
   * Create the playlist.
   */
  create() {
    playlistCreate(this.state.playlist)
      .then(playlist => {
        setMessageForNextPageLoad('The playlist has been created.');
        window.location = '/playlists/' + playlist.id
      })
      .catch(({ body }) => this.setState({ errors: body })
    );
  }

  render() {
    const { profile, classes } = this.props;
    const { playlist, errors } = this.state;
    const channels = profile ? profile.channels : [];

    // only shown the form if the user has any channel with edit rights.
    if (channels.length === 0) {
      return (
        <Typography variant="headline" component="div" className={classes.heading}>
          You have no channels in which create a playlist.
        </Typography>
      );
    }

    return (
      <section className={classes.section}>
        <Grid container justify='center'>
          <Grid item xs={12} sm={10} md={8} lg={6}>
            <Typography variant="headline" component="div" className={classes.heading}>
              Create a new playlist.
            </Typography>
            <ChannelSelect errors={ errors.channelId } channelId={ playlist.channelId } onChange={
              event => this.setState({playlist: {...playlist, channelId: event.target.value}})
            } />
            <ItemMetadataForm
              item={playlist}
              errors={errors}
              onChange={patch => this.setState({playlist: {...playlist, ...patch}})}
            />
            <div className={ classes.buttonSet }>
              <Button variant='outlined' href='/' >Cancel</Button>
              <Button color='secondary' variant='contained' onClick={ () => this.create() } >
                Create
              </Button>
            </div>
          </Grid>
        </Grid>
      </section>
    );
  }
}

const styles = theme => ({
  buttonSet: {
    '& button': {
      marginLeft: theme.spacing.unit,
    },
    marginTop: theme.spacing.unit,
    textAlign: 'right',
  },
  heading: {
    marginBottom: theme.spacing.unit * 2,
  },
  section: {
    marginTop: theme.spacing.unit,
  },
});

const ConnectedPlaylistCreatePageContents = withStyles(styles)(withProfile(PlaylistCreatePageContents));

const PlaylistCreatePage = () => (
  <Page>
    <ConnectedPlaylistCreatePageContents />
  </Page>
);

export default PlaylistCreatePage;
