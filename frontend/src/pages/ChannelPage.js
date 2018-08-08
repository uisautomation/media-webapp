import React, { Component } from 'react';

import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import { channelGet, mediaList, mediaResourceToItem } from '../api';
import MediaList from '../components/MediaList';
import RenderedMarkdown from '../components/RenderedMarkdown';
import SearchResultsProvider, { withSearchResults } from '../providers/SearchResultsProvider';
import Page from "../components/Page";

/**
 * A list of media for a channel. Upon mount, it fetches the channel details and then a list of the
 * media items and shows them to the user.
 */
class ChannelPage extends Component {
  constructor() {
    super();

    this.state = {
      // The channel resource
      channel: null,

      // Is the media list loading.
      mediaLoading: false,

      // The media list response from the API, if any.
      mediaResponse: null,
    }
  }

  componentWillMount() {
    // As soon as the index page mounts, fetch the channel.
    const { match: { params: { pk }  } } = this.props;
    channelGet(pk)
      .then(channel => {
        this.setState({ channel, mediaLoading: true });
        return mediaList({ ordering: '-updated_at' }, { endpoint: channel.mediaUrl });
      }).then(
        response => this.setState({ mediaResponse: response, mediaLoading: false }),
        error => this.setState({ mediaResponse: null, mediaLoading: false })
      );
  }


  render() {
    const { channel, mediaLoading, mediaResponse } = this.state;
    return (
      <Page>
      {
        channel !== null
        ?
        <MediaListSection
          title={ channel.title }
          description={ channel.description }
          MediaListProps={{
            contentLoading: mediaLoading,
            maxItemCount: 18,
            mediaItems: (
              (mediaResponse && mediaResponse.results)
              ? mediaResponse.results.map(mediaResourceToItem)
              : []
            ),
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

const styles = theme => ({
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

export default ChannelPage;
