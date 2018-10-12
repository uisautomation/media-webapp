import * as PropTypes from 'prop-types';
import * as React from 'react';

import { Theme } from '@material-ui/core/styles/createMuiTheme';
import createStyles from '@material-ui/core/styles/createStyles';
import withStyles, { WithStyles } from '@material-ui/core/styles/withStyles';

const styles = (theme: Theme) => createStyles({
  root: {
    paddingLeft: theme.spacing.unit * 2,
    paddingRight: theme.spacing.unit * 2,

    [theme.breakpoints.up('sm')]: {
      paddingLeft: theme.spacing.unit * 3,
      paddingRight: theme.spacing.unit * 3,
    },
  },

  gutterBottom: {
    marginBottom: theme.spacing.unit * 2,
  },
});

export interface IProps extends WithStyles<typeof styles> {
  children: React.ReactNode[];

  component: React.ReactType;

  gutterBottom: boolean;

  // Extra props to pass to the component. Use this only if the props clash with one of the props
  // used by BodySection.
  componentProps?: { [x: string]: any };

  // Indicates that unknown props are also accepted.
  [prop: string]: any;
}

/**
 * A ``<section>``-like component which defaults to the correct left/right padding for body text
 * within the application. Use instead of ``<section>`` where you want consistent left/right
 * margins for the element.
 *
 * Unknown props (including ``classes``) are broadcast to the root element.
 */
const BodySection: React.SFC<IProps> = (
  { classes, children, component: Component, gutterBottom, componentProps, ...otherProps }
) => (
  <Component
    className={ [classes.root, gutterBottom ? classes.gutterBottom : ''].join(' ') }
    classes={classes} {...componentProps} {...otherProps}
  >
    { children }
  </Component>
);

// Until we're entirely typescript, we still need propTypes to do runtime type checking.

BodySection.propTypes = {
  /** Component used for the section */
  component: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),

  /** Should extra margin be added to the bottom? */
  gutterBottom: PropTypes.bool,
};

BodySection.defaultProps = {
  component: 'section',
  gutterBottom: false,
};

export default withStyles(styles, { name: 'BodySection' })(BodySection);
