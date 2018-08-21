import React from 'react';

import Grid from '@material-ui/core/Grid';
import { withStyles } from '@material-ui/core/styles';

import Page from '../containers/Page';
import UploadForm from '../containers/UploadForm';
import RequiresEdit from "../containers/RequiresEdit";

/**
 * A page which allows the user to upload a new media item. Uses NewMediaItemProvider and
 * UploadEndpointProvider (through ConnectedUploadForm) to connect an upload form.
 */
const UploadPage = ({ classes }) => (
  <Page>
    <section className={ classes.section }>
      <RequiresEdit displayOnFalse="You have no channels to add media to.">
        <Grid container justify='center'>
          <Grid item xs={12} sm={10} md={8} lg={6}>
            <UploadForm />
          </Grid>
        </Grid>
      </RequiresEdit>
    </section>
  </Page>
);

const styles = theme => ({
  section: {
    marginTop: theme.spacing.unit,
  },
});

export default withStyles(styles)(UploadPage);
