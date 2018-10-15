import React from 'react';
import PropTypes from 'prop-types';

import { Link } from 'react-router-dom'

import Avatar from '@material-ui/core/Avatar';
import Button from '@material-ui/core/Button';
import Divider from '@material-ui/core/Divider';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import ListSubheader from '@material-ui/core/ListSubheader';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import FeedbackIcon from '@material-ui/icons/Feedback';
import HomeIcon from '@material-ui/icons/Home';
import SignOutIcon from '@material-ui/icons/ExitToApp';

import ChannelsMuiList from './ChannelsMuiList';

/** Side panel for the current user providing navigation links. */
const NavigationPanel = ({ profile, classes }) => <div className={ classes.root }>
  {
    profile && !profile.isAnonymous
    ?
    <div>
      <div className={ classes.profileBar }>
        <Avatar
          alt={ profile.displayName }
          classes={{ root: classes.avatar }}
          src={ profile.avatarImageUrl }
        >
          { profile.avatarImageUrl ? null : profile.displayName[0] }
        </Avatar>
        <Typography variant='title'>{ profile.displayName }</Typography>
        <div className={ classes.profileUsernameContainer }>
          <Typography variant='caption' className={ classes.profileUsername }>
            { profile.username }
          </Typography>
        </div>
      </div>
      <Divider />
    </div>
    :
    null
  }
  <div className={ classes.mainContent }>
    <List>
      <ListItem button component={Link} to='/'>
        <ListItemIcon><HomeIcon /></ListItemIcon>
        <ListItemText primary="Home" />
      </ListItem>
    </List>
    {
      // Do not show channel list if user has no channels.
      // TODO: when channel creation is enabled, replace this with a list which is always present
      // and which has a "create channel" item.
      profile && profile.channels && (profile.channels.length > 0)
      ?
      <div>
        <Divider />
        <ChannelsMuiList
          subheader={ <ListSubheader>Channels</ListSubheader> }
          channels={ (profile && profile.channels) || [] }
          trimCount={ 3 }
        />
      </div>
      :
      null
    }
    <Divider />
    <List>
      {
        profile && profile.isAnonymous
        ?
        <ListItem button component='a' href='/accounts/login'>
          <ListItemIcon><SignOutIcon /></ListItemIcon>
          <ListItemText primary="Sign in" />
        </ListItem>
        :
        null
      }
      <ListItem button component='a'href='mailto:media@uis.cam.ac.uk'>
        <ListItemIcon><FeedbackIcon /></ListItemIcon>
        <ListItemText primary="Feedback" />
      </ListItem>
      {
        profile && !profile.isAnonymous
        ?
        <ListItem button component='a' href='/accounts/logout'>
          <ListItemIcon><SignOutIcon /></ListItemIcon>
          <ListItemText primary="Sign out" />
        </ListItem>
        :
        null
      }
    </List>
  </div>
  <div>
    <Divider />
    <div className={ classes.bottomPanel }>
      <Typography variant='caption' gutterBottom className={ classes.bottomLinks }>
        <Link to='/about'>About</Link>
        <a href="mailto:media@uis.cam.ac.uk">Contact</a>
        <a href="https://github.com/uisautomation/media-webapp">Developers</a>
      </Typography>
      <Typography variant='caption'>
        &copy; 2018 University of Cambridge
    </Typography>
    </div>
  </div>
</div>;

NavigationPanel.propTypes = {
  /** User profile. */
  profile: PropTypes.shape({
    avatarImageUrl: PropTypes.string,
    displayName: PropTypes.string,
    isAnonymous: PropTypes.bool.isRequired,
    username: PropTypes.string,
  }),
};

const styles = theme => ({
  root: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  },

  mainContent: {
    flexGrow: 1,
  },

  bottomPanel: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    paddingBottom: theme.spacing.unit * 2,
    paddingLeft: theme.spacing.unit * 3,
    paddingRight: theme.spacing.unit * 3,
    paddingTop: theme.spacing.unit * 2,

    '& a': {
      color: 'inherit',
      textDecoration: 'inherit',
    },

    '& a:hover': {
      textDecoration: 'underline',
    },
  },

  bottomLinks: {
    '& > a': {
      marginRight: theme.spacing.unit,
    },
  },

  avatar: {
    marginBottom: theme.spacing.unit * 2,
  },

  profileBar: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    padding: theme.spacing.unit * 2,

    [theme.breakpoints.up('sm')]: {
      paddingLeft: theme.spacing.unit * 3,
      paddingRight: theme.spacing.unit * 3,
    },
  },

  profileUsernameContainer: {
    display: 'flex',
  },

  profileUsername: {
    flexGrow: 1,
  },
});

export default withStyles(styles)(NavigationPanel);
