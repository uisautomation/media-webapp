import React, { Component } from 'react';

import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import { playlistGet, mediaResourceToItem } from '../api';
import MediaList from '../components/MediaList';
import RenderedMarkdown from '../components/RenderedMarkdown';
import Page from "../containers/Page";

/**
 * A list of media for a playlist. Upon mount, it fetches the playlist with a list of the
 * media items and shows them to the user.
 */
class PlaylistPage extends Component {
  constructor() {
    super();

    this.state = {
      // The playlist resource
      playlist: null,
    }
  }

  componentWillMount() {
    // As soon as the index page mounts, fetch the playlist.
    const { match: { params: { pk } } } = this.props;
    playlistGet(pk)
      .then(playlist => {
        this.setState({ playlist });
      });
  }

  render() {
    const { playlist } = this.state;
    return (
      <Page>
      {
        playlist !== null
        ?
        <MediaListSection
          title={ playlist.title }
          description={ playlist.description }
          MediaListProps={{
            contentLoading: false,
            maxItemCount: 18,
            mediaItems: playlist.items.map(mediaResourceToItem),
          }}
        />
        :
        null
      }
      </Page>
    );
  }
}

const mediaListSectionStyles = theme => ({
  root: {
    marginBottom: theme.spacing.unit * 4,
    marginTop: theme.spacing.unit * 2,
  },
});

/** A section of the body with a heading and a MediaList. */
const MediaListSection = withStyles(mediaListSectionStyles)((
  { classes, title, description, MediaListProps, ...otherProps }
) => (
  <section className={classes.root} {...otherProps}>
    <Typography variant='display1' gutterBottom>
      { title }
    </Typography>
    <Typography variant='body1' component='div'>
      <RenderedMarkdown source={ description } />
    </Typography>
    <Typography variant='headline' gutterBottom>
      Media items
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

export default PlaylistPage;
