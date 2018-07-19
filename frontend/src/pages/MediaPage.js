import React, { Component } from 'react';
import PropTypes from 'prop-types';

import Typography from '@material-ui/core/Typography';
import Grid from '@material-ui/core/Grid';
import { withStyles } from '@material-ui/core/styles';

import { BASE_SMS_URL } from '../api';
import Page from '../components/Page';
import RenderedMarkdown from '../components/RenderedMarkdown';

/**
 * The media item page
 */
const MediaPage = ({ mediaItem, classes }) => (
  <Page>
    <section>
      <Grid container spacing={16} className={ classes.gridContainer }>
        <Grid item xs={12} className={ classes.playerWrapper } style={{paddingBottom:'56.25%'}}>
          <iframe src={mediaItem.player_url} className={ classes.player } width="100%" height="100%" frameBorder="0" allowFullScreen>
          </iframe>
        </Grid>
        <Grid item xs={12}>
          <Typography variant="headline" component="div">{ mediaItem.title }</Typography>
        </Grid>
        <Grid item xs={12}>
          <RenderedMarkdown source={ mediaItem.description }/>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="subheading">
            <a target='_blank' className={ classes.link } href={mediaItem.bestSource.url} download>
              Download media
            </a>
          </Typography>
        </Grid>
        <Grid item xs={6} style={{textAlign: 'right'}}>
          <Typography variant="subheading">
            <a className={ classes.link } href={mediaItem.statsUrl}>
              Statistics
            </a>
          </Typography>
        </Grid>
      </Grid>
    </section>
  </Page>
);

MediaPage.propTypes = {
  classes: PropTypes.object.isRequired,
};

/**
 * A higher-order component wrapper which passes the media item to its child. At the moment the media
 * item is simply resolved from global data. The wrapper also en-riches the item by:
 *
 *  - selecting the best download source to use.
 *  - creating a link to the legacy statistics page
 */
const withMediaItem = WrappedComponent => props => {

  const mediaItem = window.mediaItem;

  // select the best download source to use.

  mediaItem.bestSource = null;

  for (let i = 0; i < mediaItem.sources.length; i++) {

    if (!mediaItem.bestSource) {
      mediaItem.bestSource = mediaItem.sources[i];
    }

    if (mediaItem.sources[i].mime_type === "video/mp4") {
      if (mediaItem.bestSource.mime_type !== mediaItem.sources[i].mime_type) {
        mediaItem.bestSource = mediaItem.sources[i];
      }
      if (mediaItem.bestSource.height < mediaItem.sources[i].height) {
        mediaItem.bestSource = mediaItem.sources[i];
      }
    }
  }

  // create a link to the legacy statistics page

  mediaItem.statsUrl = BASE_SMS_URL + '/media/' + mediaItem.media_id + '/statistics';

  return (<WrappedComponent mediaItem={mediaItem} {...props} />);
};

/* tslint:disable object-literal-sort-keys */
var styles = theme => ({
  gridContainer: {
    maxWidth: 1260,
    margin: '0 auto'
  },
  playerWrapper: {
    position:'relative',
    overflow:'hidden'
  },
  player: {
    position:'absolute'
  },
  link: {
    color: theme.palette.text.secondary,
  },
});
/* tslint:enable */

export default withMediaItem(withStyles(styles)(MediaPage));
