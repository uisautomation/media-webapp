import React, { Component } from 'react';

import Button from '@material-ui/core/Button';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';
import EditIcon from '@material-ui/icons/Edit';

import { playlistGet, mediaResourceToItem } from '../api';
import MediaList from '../components/MediaList';
import RenderedMarkdown from '../components/RenderedMarkdown';
import Page from "../containers/Page";
import IfOwnsChannel from "../containers/IfOwnsChannel";

/**
 * A list of media for a playlist. Upon mount, it fetches the playlist with a list of the
 * media items and shows them to the user.
 */
class PlaylistPage extends Component {
  constructor(props) {
    super(props);

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
          playlist={ playlist }
          MediaListProps={{
            contentLoading: false,
            maxItemCount: 18,

            mediaItems: playlist.media.map(mediaResourceToItem),
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
  rightIcon: {
    marginLeft: theme.spacing.unit,
  },
  root: {
    marginBottom: theme.spacing.unit * 4,
    marginTop: theme.spacing.unit * 2,
  },
  title: {
    marginRight: theme.spacing.unit * 2,
  },
  toolbar: {
    paddingLeft: 0,
  },
});

/** A section of the body with a heading and a MediaList. */
const MediaListSection = withStyles(mediaListSectionStyles)(({
  classes, playlist: { id, channel, title, description }, MediaListProps, ...otherProps
}) => {
  return (
    <section className={classes.root} {...otherProps}>
      <Toolbar className={classes.toolbar}>
        <Typography variant='display1' className={classes.title}>
          {title}
        </Typography>
        <IfOwnsChannel channel={channel}>
          <Button component='a' color='primary' variant='contained'
                  href={'/playlists/' + id + '/edit'}
          >
            Edit
            <EditIcon className={classes.rightIcon}/>
          </Button>
        </IfOwnsChannel>
      </Toolbar>
      <Typography variant='body1' component='div'>
        <RenderedMarkdown source={description}/>
      </Typography>
      <Typography variant='headline' gutterBottom>
        Media items
      </Typography>
      <Typography component='div' paragraph>
        <MediaList
          GridItemProps={{xs: 12, sm: 6, md: 4, lg: 3, xl: 2}}
          maxItemCount={18}
          {...MediaListProps}
        />
      </Typography>
    </section>
  )
});

export default PlaylistPage;
