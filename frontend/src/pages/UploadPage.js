import React from 'react';

import Grid from '@material-ui/core/Grid';

import Page from '../containers/Page';
import UploadForm from '../containers/UploadForm';

/**
 * A page which allows the user to upload a new media item. Uses NewMediaItemProvider and
 * UploadEndpointProvider (through ConnectedUploadForm) to connect an upload form.
 */
const UploadPage = () => (
  <Page>
    <Grid container justify='center'>
      <Grid item xs={12} sm={10} md={8} lg={6}>
        <UploadForm />
      </Grid>
    </Grid>
  </Page>
);

export default UploadPage;
