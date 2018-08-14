import React, { Component } from 'react';

import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import { mediaList, mediaResourceToItem } from '../api';
import MediaList from '../components/MediaList';
import SearchResultsProvider, { withSearchResults } from '../providers/SearchResultsProvider';
import Page from "../containers/Page";

/**
 * The index page for the web application. Upon mount, it fetches a list of the latest media items
 * and shows them to the user. If the user searches, search results are fetched and displayed in a
 * new section.
 *
 * As the application grows, these will probably need to be split into separate pages. If so, the
 * search page could conceivably be a stateless functional component.
 */
class IndexPage extends Component {
  constructor() {
    super();

    // check to see if there are any search params
    const params = new URLSearchParams(location.search);
    const search = params.get('q');

    this.state = {
      // Is the latest media list loading.
      latestMediaLoading: false,

      // The latest media list response from the API, if any.
      latestMediaResponse: null,

      // Is a search query defined/loading?
      searchQuery: search ? { search } : null,
    }
  }

  componentWillMount() {
    // As soon as the index page mounts, fetch the latest media.
    this.setState({ latestMediaLoading: true });
    mediaList({ ordering: '-published_at' }).then(
      response => this.setState({ latestMediaResponse: response, latestMediaLoading: false }),
      error => this.setState({ latestMediaResponse: null, latestMediaLoading: false })
    );
  }

  handleSearch(search) {
    this.setState({ searchQuery: { search } });
  }

  render() {
    const { searchQuery, latestMediaLoading, latestMediaResponse } = this.state;
    return (
      <Page defaultSearch={searchQuery ? searchQuery.search : null}>
        <SearchResultsProvider query={searchQuery}>
          <SearchResultsSection />
        </SearchResultsProvider>

        <MediaListSection
          title="Latest Media"
          MediaListProps={{
            contentLoading: latestMediaLoading,
            maxItemCount: 18,
            mediaItems: (
              (latestMediaResponse && latestMediaResponse.results)
              ? latestMediaResponse.results.map(mediaResourceToItem)
              : []
            ),
          }}
        />
      </Page>
    );
  }
}

/**
 * If there are search results, this component shows a section with the current search results in
 * it. TODO: there is currently no indication that no search results have been returned other than
 * an empty section. Some UI needs to be designed to handle this case.
 */
const SearchResultsSection = withSearchResults(({ resultItems, isLoading }) => (
  (resultItems || isLoading) ? (
    <MediaListSection
      title="Search Results"
      MediaListProps={{
        contentLoading: isLoading,
        maxItemCount: 18,
        mediaItems: resultItems,
      }}
    />
  ) : null
));

const mediaListSectionStyles = theme => ({
  root: {
    marginBottom: theme.spacing.unit * 4,
    marginTop: theme.spacing.unit * 2,
  },
});

/** A section of the body with a heading and a MediaList. */
const MediaListSection = withStyles(mediaListSectionStyles)((
  { classes, title, MediaListProps, ...otherProps }
) => (
  <section className={classes.root} {...otherProps}>
    <Typography variant='headline' gutterBottom>
      { title }
    </Typography>
    <Typography component='div' paragraph>
      <MediaList
        GridItemProps={{ xs: 12, sm: 6, md: 4, lg: 3, xl: 2 }}
        maxItemCount={18}
        {...MediaListProps}
      />
    </Typography>
  </section>
));

const styles = theme => ({
  searchPaper: {
    padding: theme.spacing.unit * 4,
  },

  itemsPaper: {
    margin: [[theme.spacing.unit * 2, 'auto']],
    padding: theme.spacing.unit,
  },

  body: {
    margin: [[0, 'auto']],
    paddingLeft: theme.spacing.unit * 2,
    paddingRight: theme.spacing.unit * 2,

    [theme.breakpoints.up('sm')]: {
      paddingLeft: theme.spacing.unit * 3,
      paddingRight: theme.spacing.unit * 3,
    },
  },
});

export default IndexPage;
