import React, { Component } from 'react';
import PropTypes from 'prop-types';

import Button from '@material-ui/core/Button';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import { mediaList, mediaResourceToItem } from '../api';
import AppBar from '../components/AppBar';
import MediaList from '../components/MediaList';
import SearchResultsProvider, { withSearchResults } from '../providers/SearchResultsProvider';
import { withProfile } from '../providers/ProfileProvider';
import withRoot from './withRoot';

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
    super()

    this.state = {
      // Is the latest media list loading.
      latestMediaLoading: false,

      // The latest media list response from the API, if any.
      latestMediaResponse: null,

      // Is the search query loading?
      searchQuery: null,
    }
  }

  componentWillMount() {
    // As soon as the index page mounts, fetch the latest media.
    this.setState({ latestMediaLoading: true });
    mediaList({ orderBy: 'date', direction: 'desc' }).then(
      response => this.setState({ latestMediaResponse: response, latestMediaLoading: false }),
      error => this.setState({ latestMediaResponse: null, latestMediaLoading: false })
    );
  }

  handleSearch(search) {
    this.setState({ searchQuery: { search } });
  }

  render() {
    const { classes } = this.props;
    const { searchQuery, latestMediaLoading, latestMediaResponse } = this.state;
    return (
      <div className={ classes.page }>
        <AppBar position="fixed" onSearch={q => this.handleSearch(q)}>
          <ProfileButton variant="flat" color="inherit" />
        </AppBar>

        <div className={classes.body}>
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
        </div>
      </div>
    );
  }
}

IndexPage.propTypes = {
  classes: PropTypes.object.isRequired,
};

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

/** A button which allows sign in if the current user is anonymous or presents their username. */
const ProfileButton = withProfile(({ profile, ...otherProps }) => {
  if(!profile) { return null; }

  if(profile.is_anonymous) {
    return (
      <Button component='a' href={profile.urls.login} {...otherProps}>
        Sign in
      </Button>
    );
  }

  return (
    <Button {...otherProps}>
      { profile.username }
    </Button>
  );
});

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
  page: {
    minHeight: '100vh',
    paddingTop: theme.spacing.unit * 8,
    width: '100%',
  },

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

export default withRoot(withStyles(styles)(IndexPage));
