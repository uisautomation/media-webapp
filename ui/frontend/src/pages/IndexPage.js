import React, { Component } from 'react';

import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import { mediaList, mediaResourceToItem } from '../api';
import BodySection from '../components/BodySection';
import MediaList from '../components/MediaList';
import FetchChannels from "../containers/FetchChannels";
import FetchPlaylists from "../containers/FetchPlaylists";
import FetchMediaItems from "../containers/FetchMediaItems";
import Page from "../containers/Page";

// check to see if there are any search params
const params = new URLSearchParams(location.search);
const windowSearchParam = params.get('q');

/**
 * The index page for the web application. Upon mount, it fetches a list of the latest media items
 * and shows them to the user. If the user searches, search results are fetched and displayed in a
 * new section.
 *
 * As the application grows, these will probably need to be split into separate pages. If so, the
 * search page could conceivably be a stateless functional component.
 */
class IndexPage extends Component {
  state = {
    // Is a search query defined/loading?
    searchQuery: windowSearchParam ? { search: windowSearchParam } : null,
  }

  handleSearch(search) {
    this.setState({ searchQuery: { search } });
  }

  render() {
    const { searchQuery, latestMediaLoading, latestMediaResponse } = this.state;
    return (
      <Page gutterTop defaultSearch={searchQuery ? searchQuery.search : null}>
        {
          searchQuery
          ?
          <div>
            <BodySection gutterBottom>
              <Typography variant='headline' gutterBottom>Matching Channels</Typography>
              <FetchChannels query={ searchQuery } />
            </BodySection>
            <BodySection gutterBottom>
              <Typography variant='headline' gutterBottom>Matching Playlists</Typography>
              <FetchPlaylists query={ searchQuery } />
            </BodySection>
            <BodySection gutterBottom>
              <Typography variant='headline' gutterBottom>Matching Media</Typography>
              <FetchMediaItems query={ searchQuery } />
            </BodySection>
          </div>
          :
          <BodySection>
            <Typography variant='headline' gutterBottom>Latest media</Typography>
            <FetchMediaItems />
          </BodySection>
        }
      </Page>
    );
  }
}

export default IndexPage;
