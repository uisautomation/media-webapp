import React from 'react';

import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';

import BodySection from '../components/BodySection';

import Page from '../containers/Page';
import UploadForm from '../containers/UploadForm';
import IfOwnsAnyChannel from "../containers/IfOwnsAnyChannel";

/**
 * A page which allows the user to upload a new media item. Uses NewMediaItemProvider and
 * UploadEndpointProvider (through ConnectedUploadForm) to connect an upload form.
 */
const UploadPage = () => (
  <Page>
    <BodySection>
      <IfOwnsAnyChannel>
        <Grid container justify='center'>
          <Grid item xs={12} sm={10} md={8} lg={6}>
            <UploadForm />
          </Grid>
        </Grid>
      </IfOwnsAnyChannel>
      <IfOwnsAnyChannel hide>
        <Typography variant="headline" component="div">
          You have no channels to add media to.
        </Typography>
      </IfOwnsAnyChannel>
    </BodySection>
  </Page>
);

export default UploadPage;
