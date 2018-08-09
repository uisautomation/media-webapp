import React from 'react';

import Button from '@material-ui/core/Button';

import {withProfile} from "../providers/ProfileProvider";

/**
 * A button which allows sign in if the current user is anonymous or presents their username. Properties
 * appropriate to the material-ui Button component (apart from ``component`` and ``href``) can be used.
 *
 * In addition to the basic component, ``ProfileButtonWithProfile`` is exported which is ``ProfileButton``
 * already wired to the profile provider.
 */
const ProfileButton = ({ profile, ...otherProps }) => {
  if(!profile) {
    return (
      <Button {...otherProps}>Sign in</Button>
    );
  }

  if(profile.isAnonymous) {
    return (
      <Button component='a' href="/accounts/login" {...otherProps}>
        Sign&nbsp;in
      </Button>
    );
  }

  return (
    <Button {...otherProps}>
      { profile.username }
    </Button>
  );
};

export default ProfileButton;
