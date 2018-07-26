import React from 'react';

import Grid from '@material-ui/core/Grid';
import { withStyles } from '@material-ui/core/styles';

import Page from '../components/Page';
import UploadForm from '../containers/UploadForm';
import NewMediaItemProvider, { withNewMediaItem } from '../providers/NewMediaItemProvider';
import UploadEndpointProvider, { withUploadEndpoint } from '../providers/UploadEndpointProvider';

/**
 * A page which allows the user to upload a new media item. Uses NewMediaItemProvider and
 * UploadEndpointProvider (through ConnectedUploadForm) to connect an upload form.
 */
const UploadPage = ({ classes }) => (
  <Page>
    <NewMediaItemProvider>
      <ConnectedUploadProvider>
        <section className={ classes.section }>
          <Grid container justify='center'>
            <Grid item xs={12} sm={10} md={8} lg={6}>
              <ConnectedUploadForm />
            </Grid>
          </Grid>
        </section>
      </ConnectedUploadProvider>
    </NewMediaItemProvider>
  </Page>
);

const ConnectedUploadProvider = withNewMediaItem(UploadEndpointProvider);

const ConnectedUploadForm = withUploadEndpoint(withNewMediaItem(
  ({ item, uploadUrl }) => <UploadForm item={ item } url={ uploadUrl }/>
));

const styles = theme => ({
  section: {
    marginTop: theme.spacing.unit,
  },
});

export default withStyles(styles)(UploadPage);
