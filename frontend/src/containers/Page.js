import React from 'react';
import PropTypes from 'prop-types';

import Drawer from '@material-ui/core/Drawer';
import IconButton from '@material-ui/core/IconButton';
import Hidden from '@material-ui/core/Hidden';
import { withStyles } from '@material-ui/core/styles';
import UploadIcon from '@material-ui/icons/CloudUpload';

import AppBar from "../components/AppBar";
import MotdBanner from "../components/MotdBanner";
import NavigationPanel from "../components/NavigationPanel";
import Snackbar from "./Snackbar";

import { withProfile } from "../providers/ProfileProvider";

const ConnectedNavigationPanel = withProfile(NavigationPanel);

/**
 * A top level component that wraps all pages to give then elements common to all page, the ``AppBar``
 * etc.
 */
class Page extends React.Component {
  state = {
    mobileDrawerOpen: false,
  };

  handleDrawerToggle = () => {
    this.setState(state => ({ mobileDrawerOpen: !state.mobileDrawerOpen }));
  };

  render() {
    const { defaultSearch, classes, children } = this.props;
    const { mobileDrawerOpen } = this.state;
    const drawer = <ConnectedNavigationPanel />;

    return (
      <div className={ classes.page }>
        <AppBar
          classes={{root: classes.appBar}}
          position='absolute'
          defaultSearch={defaultSearch}
          onMenuClick={ this.handleDrawerToggle }
        >
          <HiddenIfNoChannels>
            <IconButton color="inherit" component="a" href="/upload">
              <UploadIcon />
            </IconButton>
          </HiddenIfNoChannels>
        </AppBar>

        <Hidden mdUp>
          <Drawer
            variant="temporary"
            open={ mobileDrawerOpen }
            onClose={ this.handleDrawerToggle }
            classes={{
              paper: classes.drawerPaper,
            }}
            ModalProps={{
              keepMounted: true, // Better open performance on mobile.
            }}
          >
            { drawer }
          </Drawer>
        </Hidden>

        <Hidden smDown implementation="css">
          <Drawer
            variant="permanent"
            classes={{
              paper: classes.drawerPaper,
            }}
          >
            { /* used as a spacer */ }
            <div className={classes.toolbar} />
            { drawer }
          </Drawer>
        </Hidden>

        <div className={classes.content}>
          { /* used as a spacer */ }
          <div className={classes.toolbar} />
          <main className={classes.body}>
            <MotdBanner />
            { children }
          </main>
        </div>

        <Snackbar/>
      </div>
    );
  }
}

Page.propTypes = {
  /** @ignore */
  classes: PropTypes.object.isRequired,

  /** Default search text to populate the search form with. */
  defaultSearch: PropTypes.string,
};

const styles = theme => ({
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
  },

  drawerPaper: {
    position: 'relative',
    width: theme.dimensions.drawerWidth,
  },

  page: {
    height: '100vh',
    width: '100%',
    display: 'flex',
    overflow: 'hidden',
    display: 'flex',
  },

  content: {
    display: 'flex',
    flexDirection: 'column',
    flexGrow: 1,
  },

  body: {
    flexGrow: 1,
    overflowY: 'auto',
    paddingLeft: theme.spacing.unit * 2,
    paddingRight: theme.spacing.unit * 2,

    [theme.breakpoints.up('sm')]: {
      paddingLeft: theme.spacing.unit * 3,
      paddingRight: theme.spacing.unit * 3,
    },
  },

  toolbar: theme.mixins.toolbar,
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
