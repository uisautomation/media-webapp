import React from 'react';
import PropTypes from 'prop-types';

import { Link } from 'react-router-dom'

import Avatar from '@material-ui/core/Avatar';
import Button from '@material-ui/core/Button';
import Divider from '@material-ui/core/Divider';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import LatestMediaIcon from '@material-ui/icons/NewReleases';

/** Side panel for the current user providing navigation links. */
const NavigationPanel = ({ profile, classes }) => <div className={ classes.root }>
  <div className={ classes.profileBar }>
  {
    profile && !profile.isAnonymous
    ?
    <div>
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
    :
    null
  }
  {
    profile && profile.isAnonymous
    ?
    <div>
      <Button
        color='primary' variant='outlined' fullWidth component='a' href='/accounts/login'
      >
        Sign in with Raven
      </Button>
    </div>
    :
    null
  }
  </div>
  <Divider />
  <List>
    <ListItem button component={Link} to='/'>
      <ListItemText primary="Latest Media" />
    </ListItem>
    {
      profile && !profile.isAnonymous
      ?
      <ListItem button component='a' href='/accounts/logout'>
        <ListItemText primary="Sign out" />
      </ListItem>
      :
      null
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
