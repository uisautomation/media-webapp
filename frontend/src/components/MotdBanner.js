import React from 'react';
import PropTypes from 'prop-types';

import Typography from '@material-ui/core/Typography';
import Divider from '@material-ui/core/Divider';
import { withStyles } from '@material-ui/core/styles';

import ReleaseTag from './ReleaseTag';

/**
 * The "message of the day" banner used to display information from the admins to the users.
 *
 * Any unknown properties supplied will be spread to the root component.
 */
const MotdBanner = ({
  classes, component: Component, ...otherProps
}) => (
  <Component component='div' className={classes.root} {...otherProps}>
    <div className={classes.message}>
      <ReleaseTag style={{marginRight: '0.5ex'}}>alpha</ReleaseTag>
      {' '}This service is in development.{' '} { /* whitespace coalescing in JSX sux! */ }
      <a className={classes.link} href="/about#help-us">Help us improve it.</a>
    </div>
    <Divider />
  </Component>
)

MotdBanner.propTypes = {
  /** Base component for the control. */
  component: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
};

MotdBanner.defaultProps = {
  component: Typography,
};

const styles = theme => ({
  root: {
    marginTop: theme.spacing.unit * 2,
  },

  message: {
    paddingBottom: theme.spacing.unit,
  },

  link: {
    color: theme.palette.text.secondary,
  },
});

export default withStyles(styles)(MotdBanner);
