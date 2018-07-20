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
          <iframe src={mediaItem.embedUrl} className={ classes.player } width="100%" height="100%" frameBorder="0" allowFullScreen>
          </iframe>
        </Grid>
        <Grid item xs={12}>
          <Typography variant="headline" component="div">{ mediaItem.name }</Typography>
        </Grid>
        <Grid item xs={12}>
          <RenderedMarkdown source={ mediaItem.description }/>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="subheading">
            {
              mediaItem.contentUrl
              ?
              <a target='_blank' className={ classes.link } href={mediaItem.contentUrl} download>
                Download media
              </a>
              :
              null
            }
          </Typography>
        </Grid>
        <Grid item xs={6} style={{textAlign: 'right'}}>
          <Typography variant="subheading">
            {
              mediaItem.legacy.statisticsUrl
              ?
              <a className={ classes.link } href={mediaItem.legacy.statisticsUrl}>
                Statistics
              </a>
              :
              null
            }
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
 * item is the JSON-parsed contents of an element with id "mediaItem".
 */
const withMediaItem = WrappedComponent => props => {
  let mediaItem = null;
  const mediaItemElement = document.getElementById('mediaItem');
  if(mediaItemElement) {
    mediaItem = JSON.parse(mediaItemElement.textContent);
  }

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
