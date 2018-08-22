import React from 'react';
import PropTypes from 'prop-types';

import { withProfile } from "../providers/ProfileProvider";

/**
 * A component which renders if the user has edit permission on the given channel. If 'hide' is set,
 * the children are rendered if the user doesn't have edit permission on the given channel.
 */
const IfOwnsChannel = (
  { profile, channel, hide, component: Component, children, ...otherProps }
) => {
  // only render, if the profile is available
  if (profile && profile.channels) {
    let show = channel && profile.channels.find(chan => chan.id === channel.id);
    if (hide) {
      show = !show
    }
    if (show) {
      return <Component {...otherProps}>{ children }</Component>
    }
  }
  return <Component {...otherProps}/>
};

IfOwnsChannel.propTypes = {
  /** A channel defining the context of the component */
  channel: PropTypes.object,
  /** Component to wrap children in. */
  component: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  /** either hide or show depending on the test */
  hide: PropTypes.bool,
};

IfOwnsChannel.defaultProps = {
  component: 'div',
};

export default withProfile(IfOwnsChannel);
