import React from 'react';
import PropTypes from 'prop-types';

import { withProfile } from "../providers/ProfileProvider";

/**
 * A component which renders its children only if the user has editable permission
 * in their current context.
 */
const RequiresEdit = (
  { profile, channel, displayOnFalse, component: Component, children, ...otherProps }
) => {
  let display = '';

  if (profile && profile.channels) {
    display = displayOnFalse;

    if (channel) {
      // if a channel is given, check that the user can edit it.
      if (profile.channels.find((el) => (el.id === channel.id))) {
        display = children;
      }
    } else {
      // if no channel is given, check the user has channels they can edit.
      if (profile.channels.length > 0) {
        display = children;
      }
    }
  }
  return <Component {...otherProps}>{ display }</Component>;
};

RequiresEdit.propTypes = {
  /** A channel defining the context of the component */
  channel: PropTypes.object,
  /** Component to wrap children in. */
  component: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  /** If there isn't edit permission, display this text */
  displayOnFalse: PropTypes.string
};

RequiresEdit.defaultProps = {
  component: 'div',
};

export default withProfile(RequiresEdit);
