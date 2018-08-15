import React, { Component } from 'react';

import Button from '@material-ui/core/Button';
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';

import {withProfile} from "../providers/ProfileProvider";

/**
 * A button which allows sign in if the current user is anonymous or presents their username. Properties
 * appropriate to the material-ui Button component (apart from ``component`` and ``href``) can be used.
 *
 * In addition to the basic component, ``ProfileButtonWithProfile`` is exported which is ``ProfileButton``
 * already wired to the profile provider.
 */
class ProfileButton extends Component {
  state = { menuAnchorElement: null };

  handleClick = event => this.setState({ menuAnchorElement: event.currentTarget });

  handleClose = () => this.setState({ menuAnchorElement: null });

  render() {
    const { profile, ...otherProps } = this.props;
    const { menuAnchorElement } = this.state;

    if(!profile || profile.isAnonymous) {
      return (
        <Button component='a' href="/accounts/login" {...otherProps}>
          Sign&nbsp;in
        </Button>
      );
    }

    return <div>
      <Button onClick={ this.handleClick } {...otherProps}>
        { profile.username }
      </Button>
      <Menu
        id="profileMenu"
        anchorEl={ menuAnchorElement }
        open={ Boolean(menuAnchorElement) }
        onClose={ this.handleClose }
      >
        <MenuItem component='a' href='/accounts/logout'>
          Sign out
        </MenuItem>
      </Menu>
    </div>;
  }
}

export default ProfileButton;
