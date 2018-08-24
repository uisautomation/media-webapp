import React from 'react';
import PropTypes from 'prop-types';

import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import BodySection from '../components/BodySection';

import ReleaseTag from './ReleaseTag';

/**
 * The "message of the day" banner used to display information from the admins to the users.
 *
 * Any unknown properties supplied will be spread to the root component.
 */
const MotdBanner = ({
  classes, component: Component, ...otherProps
}) => (
  <BodySection classes={{ root: classes.root }}>
    <Typography component='div' classes={{ root: classes.message }}>
      <ReleaseTag style={{marginRight: '0.5ex'}}>alpha</ReleaseTag>
      {' '}This service is in development.{' '} { /* whitespace coalescing in JSX sux! */ }
      <a className={classes.link} href="/about#help-us">Help us improve it.</a>
    </Typography>
  </BodySection>
)

MotdBanner.propTypes = {
};

MotdBanner.defaultProps = {
};

const styles = theme => ({
  root: {
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.08)',
    borderBottom: [[1, 'solid', theme.palette.divider]],
    display: 'flex',
    marginBottom: -1,
    ...theme.mixins.toolbar,
  },

  message: { /* No default styles */ },

  link: {
    color: theme.palette.text.secondary,

    [theme.breakpoints.down('xs')]: {
      display: 'none',
    },
  },
});

export default withStyles(styles)(MotdBanner);
