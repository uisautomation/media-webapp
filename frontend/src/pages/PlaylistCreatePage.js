import React, { Component } from 'react';
import { Helmet } from 'react-helmet';

import { Link, Redirect } from 'react-router-dom'

import Button from '@material-ui/core/Button';
import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';

import { withStyles } from '@material-ui/core/styles';

import Page from '../containers/Page';
import ChannelSelect from '../containers/ChannelSelect';
import BodySection from "../components/BodySection";
import {playlistCreate} from "../api";
import { showMessage } from "../containers/Snackbar";
import IfOwnsAnyChannel from "../containers/IfOwnsAnyChannel";
import PlaylistMetadataForm from "../components/PlaylistMetadataForm";

/**
 * A page which allows the user to create a new playlist.
 */
class PlaylistCreatePageContents extends Component {
  constructor(props) {
    super(props);

    this.state = {
      // An error object as returned by the API or the empty object if there are no errors.
      errors: {},

      // The playlist being created.
      playlist: { channelId: '', title: '' },

      // Whether the playlist was successfully created.
      playlistCreated: false,
    };
  }

  /**
   * Create the playlist.
   */
  create() {
    playlistCreate(this.state.playlist)
      .then(playlist => {
        this.setState({ playlistCreated: true, playlist });
        showMessage(`Playlist "${playlist.title}" created.`);
      })
      .catch(({ body }) => this.setState({ errors: body })
    );
  }

  render() {
    const { classes } = this.props;
    const { playlist, errors, playlistCreated } = this.state;

    if(playlistCreated) {
      return <Redirect to={'/playlists/' + playlist.id} />;
    }

    return (
      <BodySection>
        <Helmet><title>Create new playlist</title></Helmet>
        <IfOwnsAnyChannel>
          <Grid container justify='center'>
            <Grid item xs={12} sm={10} md={8} lg={6}>
              <Typography variant="headline" component="div" className={classes.heading}>
                Create a new playlist.
              </Typography>
              <ChannelSelect errors={ errors.channelId } channelId={ playlist.channelId } onChange={
                event => this.setState({playlist: {...playlist, channelId: event.target.value}})
              } />
              <PlaylistMetadataForm
                playlist={playlist}
                errors={errors}
                onChange={patch => this.setState({playlist: {...playlist, ...patch}})}
              />
              <div className={ classes.buttonSet }>
                <Button variant='outlined' component={ Link } to='/' >Cancel</Button>
                <Button color='secondary' variant='contained' onClick={ () => this.create() } >
                  Create
                </Button>
              </div>
            </Grid>
          </Grid>
        </IfOwnsAnyChannel>
        <IfOwnsAnyChannel hide>
          <Typography variant="headline" component="div">
            You have no channels in which create a playlist.
          </Typography>
        </IfOwnsAnyChannel>
      </BodySection>
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
    marginTop: theme.spacing.unit,
  },
});

const ConnectedPlaylistCreatePageContents = withStyles(styles)(PlaylistCreatePageContents);

const PlaylistCreatePage = () => (
  <Page>
    <ConnectedPlaylistCreatePageContents />
  </Page>
);

export default PlaylistCreatePage;
