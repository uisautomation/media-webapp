import React from 'react';
import PropTypes from 'prop-types';

import { withProfile } from "../providers/ProfileProvider";

/**
 * A component which renders its children if the user has any editable channels. If 'hide' is set,
 * the children are rendered if the user doesn't any editable channels.
 */
const IfOwnsAnyChannel = (
  { profile, hide, component: Component, children, ...otherProps }
) => {
  // only render, if the profile is available
  if (profile && profile.channels) {
    let show = profile.channels.length > 0;
    if (hide) {
      show = !show
    }
    if (show) {
      return <Component {...otherProps}>{ children }</Component>
    }
  }
  return <Component {...otherProps}/>
};

IfOwnsAnyChannel.propTypes = {
  /** Component to wrap children in. */
  component: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  /** either hide or show depending on the test */
  hide: PropTypes.bool,
};

IfOwnsAnyChannel.defaultProps = {
  component: 'div',
};

export default withProfile(IfOwnsAnyChannel);
