import React from 'react';
import PropTypes from 'prop-types';

import Avatar from '@material-ui/core/Avatar';
import Divider from '@material-ui/core/Divider';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import LatestMediaIcon from '@material-ui/icons/NewReleases';

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
        <Typography variant='caption'>{ profile.username }</Typography>
      </div>
      <Divider />
    </div>
    :
    null
  }
  <List>
    <ListItem button component='a' href='/'>
      <ListItemText primary="Latest Media" />
    </ListItem>
    {
      profile && !profile.isAnonymous
      ?
      <ListItem button component='a' href='/accounts/logout'>
        <ListItemText primary="Sign out" />
      </ListItem>
      :
      <ListItem button component='a' href='/accounts/login'>
        <ListItemText primary="Sign in" />
      </ListItem>
    }
  </List>
</div>;

NavigationPanel.propTypes = {
  /** User profile. */
  profile: PropTypes.shape({
    avatarImageUrl: PropTypes.string,
    displayName: PropTypes.string,
    isAnonymous: PropTypes.bool.isRequired,
    username: PropTypes.string.isRequired,
  }),
};

const styles = theme => ({
  avatar: {
    marginBottom: theme.spacing.unit * 2,
  },

  profileBar: {
    ...theme.mixins.toolbar,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    padding: theme.spacing.unit * 2,

    [theme.breakpoints.up('sm')]: {
      paddingLeft: theme.spacing.unit * 3,
      paddingRight: theme.spacing.unit * 3,
    },
  }
});

export default withStyles(styles)(NavigationPanel);
