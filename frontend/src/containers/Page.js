import React from 'react';
import PropTypes from 'prop-types';

import { withStyles } from '@material-ui/core/styles';
import IconButton from '@material-ui/core/IconButton';
import UploadIcon from '@material-ui/icons/CloudUpload';
import PlaylistAddIcon from '@material-ui/icons/PlaylistAdd';

import AppBar from "../components/AppBar";
import MotdBanner from "../components/MotdBanner";
import ProfileButtonContainer from "./ProfileButtonContainer";
import Snackbar from "./Snackbar";
import IfOwnsAnyChannel from "./IfOwnsAnyChannel";

/**
 * A top level component that wraps all pages to give then elements common to all page,
 * the ``AppBar`` etc.
 */
const Page = (
  { defaultSearch, classes, children }
) => (
      <div className={ classes.page }>
        <AppBar position="fixed" defaultSearch={defaultSearch}>
          <IfOwnsAnyChannel>
            <IconButton color="inherit" component="a" href="/media/new">
              <UploadIcon />
            </IconButton>
            <IconButton color="inherit" component="a" href="/playlists/new">
              <PlaylistAddIcon />
            </IconButton>
          </IfOwnsAnyChannel>
          <ProfileButtonContainer
            className={ classes.rightButton } variant="flat" color="inherit"
          />
        </AppBar>

        <div className={classes.body}>
          <MotdBanner />
          { children }
        </div>

        <Snackbar/>
      </div>
);

Page.propTypes = {
  /** @ignore */
  classes: PropTypes.object.isRequired,

  /** Default search text to populate the search form with. */
  defaultSearch: PropTypes.string,
};

const styles = theme => ({
  page: {
    minHeight: '100vh',
    paddingTop: theme.spacing.unit * 8,
    width: '100%',
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

  rightButton: {
    marginRight: -1.5 * theme.spacing.unit,
  },
});

export default withStyles(styles)(Page);
