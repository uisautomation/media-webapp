import React, { Component } from 'react';

import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import { channelGet, mediaList, mediaResourceToItem } from '../api';
import FetchChannel from "../containers/FetchChannel";
import FetchMediaItems from "../containers/FetchMediaItems";
import BodySection from '../components/BodySection';
import MediaList from '../components/MediaList';
import RenderedMarkdown from '../components/RenderedMarkdown';
import Page from "../containers/Page";

/**
 * A list of media for a channel. Upon mount, it fetches the channel details and then a list of the
 * media items and shows them to the user.
 */
const ChannelPage = ({ match: { params: { pk } } }) => (
  <Page gutterTop><FetchChannel id={ pk } component={ PageContent } /></Page>
);

/** Channel page content. */
const PageContent = ({ resource: channel }) => (
  channel && channel.id
  ?
  <BodySection>
    <Typography variant='display1' gutterBottom>{ channel.title }</Typography>
    <RenderedMarkdown source={ channel.description } />
    <Typography variant='headline' gutterBottom>Media items</Typography>
    <FetchMediaItems query={{ channel: channel.id }} />
  </BodySection>
  :
  null
);

export default ChannelPage;
