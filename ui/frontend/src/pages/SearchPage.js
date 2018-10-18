import React, { Component } from 'react';

import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import BodySection from '../components/BodySection';
import FetchChannels from "../containers/FetchChannels";
import FetchPlaylists from "../containers/FetchPlaylists";
import FetchMediaItems from "../containers/FetchMediaItems";
import Page from "../containers/Page";

// check to see if there are any search params
const params = new URLSearchParams(location.search);
const search = params.get('q');

/**
 * The page for displaying the search results. It retrieves the media items, playlists, and
 * channels for the search critieria simultaneously and shows them to the user.
 */
class SearchPage extends Component {
  render() {
    return (
      <Page gutterTop defaultSearch={ search }>
        <div>
          <BodySection gutterBottom>
            <Typography variant='headline' gutterBottom>Matching Channels</Typography>
            <FetchChannels query={{ search: search }} />
          </BodySection>
          <BodySection gutterBottom>
            <Typography variant='headline' gutterBottom>Matching Playlists</Typography>
            <FetchPlaylists query={{ search: search }} />
          </BodySection>
          <BodySection gutterBottom>
            <Typography variant='headline' gutterBottom>Matching Media</Typography>
            <FetchMediaItems query={{ search: search }} />
          </BodySection>
        </div>
      </Page>
    );
  }
}

export default SearchPage;
