import React from 'react';
import PropTypes from 'prop-types';

import { withStyles } from '@material-ui/core/styles';

/**
 * A tag used to indicate that the webapp is at a particular release stage.
 *
 * Any unknown properties supplied will be spread to the root component.
 */
const ReleaseTag = ({
  classes, component: Component, color, children, ...otherProps
}) => (
  <Component
    className={[
      classes.root,
      color === 'default' ? classes.colorDefault : null,
      color === 'primary' ? classes.colorPrimary : null,
      color === 'secondary' ? classes.colorSecondary : null
    ].join(' ')}
    {...otherProps}
  >
    { children }
  </Component>
)

ReleaseTag.propTypes = {
  /** The color of the component. */
  color: PropTypes.oneOf(['default', 'primary', 'secondary', 'inherit']),

  /** Base component for the control. */
  component: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
};

ReleaseTag.defaultProps = {
  color: 'default',
  component: 'span',
};

const styles = theme => ({
  root: {
    borderRadius: theme.spacing.unit * 0.5,
    display: 'inline-block',
    padding: [[theme.spacing.unit * 0.5, theme.spacing.unit]],
    textTransform: 'uppercase',
  },

  colorDefault: {
    backgroundColor: theme.palette.getContrastText(theme.palette.background.default),
    color: theme.palette.background.default,
  },

  colorPrimary: {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
  },

  colorSecondary: {
    backgroundColor: theme.palette.secondary.main,
    color: theme.palette.secondary.contrastText,
  },
});

export default withStyles(styles)(ReleaseTag);
