import React, { Component } from 'react';

import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import { playlistGet, mediaList, mediaResourceToItem } from '../api';
import FetchPlaylist from "../containers/FetchPlaylist";
import FetchMediaItems from "../containers/FetchMediaItems";
import BodySection from '../components/BodySection';
import MediaList from '../components/MediaList';
import RenderedMarkdown from '../components/RenderedMarkdown';
import Page from "../containers/Page";

/**
 * A list of media for a playlist. Upon mount, it fetches the playlist details and then a list of the
 * media items and shows them to the user.
 */
const PlaylistPage = ({ match: { params: { pk } } }) => (
  <Page gutterTop><FetchPlaylist id={ pk } component={ PageContent } /></Page>
);

/** Playlist page content. */
const PageContent = ({ resource: playlist }) => (
  playlist && playlist.id
  ?
  <BodySection>
    <Typography variant='display1' gutterBottom>{ playlist.title }</Typography>
    <RenderedMarkdown source={ playlist.description } />
    <Typography variant='headline' gutterBottom>Media items</Typography>
    <FetchMediaItems query={{ playlist: playlist.id }} />
  </BodySection>
  :
  null
);

export default PlaylistPage;

