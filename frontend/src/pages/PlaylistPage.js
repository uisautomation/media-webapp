import React, { Component } from 'react';

import Button from '@material-ui/core/Button';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';
import EditIcon from '@material-ui/icons/Edit';

import FetchPlaylist from "../containers/FetchPlaylist";
import BodySection from '../components/BodySection';
import RenderedMarkdown from '../components/RenderedMarkdown';
import Page from "../containers/Page";
import IfOwnsChannel from "../containers/IfOwnsChannel";
import MediaList from "../components/MediaList";

/**
 * A list of media for a playlist. Upon mount, it fetches the playlist details and then a list of the
 * media items and shows them to the user.
 */
const PlaylistPage = ({ match: { params: { pk } } }) => (
  <Page gutterTop><FetchPlaylist id={ pk } component={ PageContent } /></Page>
);

const pageContentStyles = theme => ({
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

/** Playlist page content. */
const PageContent = withStyles(pageContentStyles)(({ classes, resource: playlist }) => (
  playlist && playlist.id
  ?
  <BodySection>
    <Toolbar className={classes.toolbar}>
      <Typography variant='display1' className={classes.title}>
        { playlist.title }
      </Typography>
      <IfOwnsChannel channel={playlist.channel}>
        <Button component='a' color='primary' variant='contained'
                href={'/playlists/' + playlist.id + '/edit'}
        >
          Edit
          <EditIcon className={classes.rightIcon}/>
        </Button>
      </IfOwnsChannel>
    </Toolbar>
    <RenderedMarkdown source={ playlist.description } />
    <Typography variant='headline' gutterBottom>Media items</Typography>
    <MediaList resources={playlist.media} />
  </BodySection>
  :
  null
));

export default PlaylistPage;

