import React, { Component } from 'react';

import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import BodySection from '../components/BodySection';
import FetchMediaItems from "../containers/FetchMediaItems";
import Page from "../containers/Page";

/**
 * The index page for the web application. Upon mount, it fetches a list of the latest media items
 * and shows them to the user.
 */
const IndexPage = () => (
  <Page gutterTop>
    <BodySection>
      <Typography variant='headline' gutterBottom>Latest media</Typography>
      <FetchMediaItems />
    </BodySection>
  </Page>
);

export default IndexPage;
