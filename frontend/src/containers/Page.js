import React from 'react';
import PropTypes from 'prop-types';

import { withStyles } from '@material-ui/core/styles';
import IconButton from '@material-ui/core/IconButton';
import UploadIcon from '@material-ui/icons/CloudUpload';

import AppBar from "../components/AppBar";
import MotdBanner from "../components/MotdBanner";
import ProfileButtonContainer from "./ProfileButtonContainer";
import Snackbar from "./Snackbar";

import { withProfile } from "../providers/ProfileProvider";

/**
 * A top level component that wraps all pages to give then elements common to all page, the ``AppBar``
 * etc.
 */
const Page = (
  { defaultSearch, classes, children }
) => (
      <div className={ classes.page }>
        <AppBar position="fixed" defaultSearch={defaultSearch}>
          <HiddenIfNoChannels>
            <IconButton color="inherit" component="a" href="/upload">
              <UploadIcon />
            </IconButton>
          </HiddenIfNoChannels>
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

/** A component which renders its children only if the profile has editable channels. */
const HiddenIfNoChannels = withProfile(({ profile, children, component: Component }) => (
  <Component>
    {
      (profile && profile.channels && (profile.channels.length > 0))
      ?
      children
      :
      null
    }
  </Component>
));

HiddenIfNoChannels.propTypes = {
  /** Component to wrap children in. */
  component: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
};

HiddenIfNoChannels.defaultProps = {
  component: 'div',
};
