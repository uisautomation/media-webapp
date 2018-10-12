import React from 'react';
import PropTypes from 'prop-types';

import Button from '@material-ui/core/Button';
import Input from '@material-ui/core/Input';

import Search from '@material-ui/icons/Search';

import { withStyles } from '@material-ui/core/styles';

/**
 * A combined input field and submit button providing a horizontal search control form.
 *
 * Any unknown properties supplied will be spread to the root component.
 */
const SearchForm = ({
  classes, component: Component, InputProps, ButtonProps, color, autoFocus, ...otherProps
}) => (
  <Component
    className={[
      classes.root,
      color === 'primary' ? classes.colorPrimary : null,
      color === 'secondary' ? classes.colorSecondary : null
    ].join(' ')}
    {...otherProps}
  >
    <Input
      disableUnderline
      fullWidth
      autoFocus={autoFocus}
      type='search'
      classes={{
        input: classes.searchInputInput,
        root: classes.searchInputRoot,
      }}
      {...InputProps}
    />
    <Button
      variant='raised' size='large' color={color} type='submit'
      classes={{
        root: classes.searchButtonRoot,
      }}
      {...ButtonProps}
    >
      <Search />
    </Button>
  </Component>
);

SearchForm.propTypes = {
  /** If true, the search form input will be focussed. */
  autoFocus: PropTypes.bool,

  /** The color of the component. */
  color: PropTypes.oneOf(['default', 'primary', 'secondary', 'inherit']),

  /** Base component for the control. */
  component: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),

  /** Props passed to the ``Input`` element implementing the search field. */
  InputProps: PropTypes.object,

  /** Props passed to the ``Button`` element implementing the submit button. */
  ButtonProps: PropTypes.object,
};

SearchForm.defaultProps = {
  autoFocus: false,
  color: 'default',
  component: 'form',
};

const styles = theme => ({
  root: {
    backgroundColor: theme.palette.background.paper,
    border: [[1, 'solid', theme.palette.divider]],
    borderRadius: theme.spacing.unit * 0.5,
    display: 'flex',
    overflow: 'hidden',
  },

  colorPrimary: {
    border: [[1, 'solid', theme.palette.primary.main]],
  },

  colorSecondary: {
    border: [[1, 'solid', theme.palette.secondary.main]],
  },

  searchInputRoot: {
    padding: [[ theme.spacing.unit, theme.spacing.unit*2 ]],
  },

  searchInputInput: {
    background: 'none',
    height: theme.spacing.unit * 3,
    minWidth: theme.spacing.unit * 5,
    padding: 0,
  },

  searchButtonRoot: {
    borderRadius: 0,
    boxShadow: 'none',
    height: theme.spacing.unit * 5,
    minWidth: theme.spacing.unit * 6,
    padding: 0,
  },
});

export default withStyles(styles)(SearchForm);
