import * as React from 'react';

import Button, { ButtonProps as ButtonPropsType } from '@material-ui/core/Button';
import Input, { InputProps as InputPropsType } from '@material-ui/core/Input';

import { createStyles, Theme, withStyles, WithStyles } from '@material-ui/core/styles';

import SearchIcon from '@material-ui/icons/Search';

const styles = (theme: Theme) => createStyles({
  root: {
    backgroundColor: theme.palette.background.paper,
    border: `1px solid ${theme.palette.divider}`,
    borderRadius: theme.spacing.unit * 0.5,
    display: 'flex',
    overflow: 'hidden',
  },

  colorPrimary: {
    border: `1px solid ${theme.palette.primary.main}`,
  },

  colorSecondary: {
    border: `1px solid ${theme.palette.secondary.main}`,
  },

  searchInputRoot: {
    padding: `${theme.spacing.unit}px ${theme.spacing.unit * 2}px`,
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

export interface IProps extends WithStyles<typeof styles> {
  /** If true, the search form input will be focussed. */
  autoFocus: boolean;

  /** The color of the component. */
  color: 'default' | 'primary' | 'secondary' | 'inherit';

  /** Base component for the control. */
  component: React.ComponentClass<any> | React.StatelessComponent<any> | string;

  /** Props for Input element. */
  InputProps: InputPropsType,

  /** Props passed to the ``Button`` element implementing the submit button. */
  ButtonProps: ButtonPropsType,

  /** Other props are spread to the root component. */
  [x: string]: any;
}

/**
 * A combined input field and submit button providing a horizontal search control form.
 *
 * Any unknown properties supplied will be spread to the root component.
 */
export const SearchForm: React.SFC<IProps> = ({
  classes,

  autoFocus,
  color,
  component: Component,

  ButtonProps,
  InputProps,

  ...otherProps
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
      disableUnderline={ true }
      fullWidth={ true }
      autoFocus={ autoFocus }
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
      <SearchIcon />
    </Button>
  </Component>
);

SearchForm.defaultProps = {
  autoFocus: false,
  color: 'default',
  component: 'form',
};

export default withStyles(styles)(SearchForm);
