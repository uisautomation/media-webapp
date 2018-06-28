import React from 'react';
import PropTypes from 'prop-types';

import MuiAppBar from '@material-ui/core/AppBar';
import Button from '@material-ui/core/Button';
import Grid from '@material-ui/core/Grid';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import SearchForm from './SearchForm';

const styles = theme => ({
  root: { /* no default styles */ },

  appBarLeft: {
    display: 'flex',
    justifyContent: 'flex-start',
    paddingRight: theme.spacing.unit * 3,

    [theme.breakpoints.down('sm')]: {
      display: 'none',
    }
  },

  appBarMiddle: {
    display: 'flex',
    justifyContent: 'center',
  },

  appBarRight: {
    display: 'flex',
    justifyContent: 'flex-end',
    paddingLeft: theme.spacing.unit * 3,

    [theme.breakpoints.down('xs')]: {
      display: 'none',
    }
  },

  searchFormRoot: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    border: 'none',
    maxWidth: '640px',
    width: '100%',
  },

  searchFormButtonRoot: {
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    color: theme.palette.common.white,
  },

  searchFormInputRoot: {
    color: theme.palette.common.white,
  },
});

/**
 * AppBar component for the media service. Children appear in the right-most part of the bar for
 * larger screen sizes.
 *
 * Any unknown properties supplied will be spread to the root component.
 */
const AppBar = (
  { classes, onSearch, color, children, autoFocus, ...otherProps }
) => (
  <MuiAppBar position="static" color={color} className={classes.root} {...otherProps}>
    <Grid container component={Toolbar}>
      <Grid item xs={3} className={classes.appBarLeft}>
        <Typography variant="title" color="inherit">
          University Media Platform
        </Typography>
      </Grid>
      <Grid item xs={12} sm={9} md={6} className={classes.appBarMiddle}>
        <SearchForm
          autoFocus={autoFocus}
          color={color}
          classes={{
            root: classes.searchFormRoot,
            searchButtonRoot: classes.searchFormButtonRoot,
            searchInputRoot: classes.searchFormInputRoot,
          }}
          onSubmit={event => handleSubmit(event, onSearch)}
          InputProps={{
            name: 'q',
            placeholder: 'Search',
          }}
        />
      </Grid>
      <Grid item xs={3} className={classes.appBarRight}>
        { children }
      </Grid>
    </Grid>
  </MuiAppBar>
);

AppBar.propTypes = {
  /** If true, the search form input will be focussed. */
  autoFocus: PropTypes.bool,

  /** The color of the component. */
  color: PropTypes.oneOf(['default', 'inherit', 'primary', 'secondary']),

  /** Function called with search text. */
  onSearch: PropTypes.func,
};

AppBar.defaultProps = {
  autoFocus: true,
  color: 'primary',
};

const handleSubmit = (event, onSearch) => {
  // Prevent default handling of submit event.
  event.preventDefault();

  // Need do nothing else if there is no search handler.
  if(!onSearch) { return; }

  // Get value from input element.
  const formElement = event.target;
  const inputElement = Array.from(formElement.elements).filter(element => element.name === 'q')[0];
  if(!inputElement) { return; }

  // Get query from input element.
  const query = inputElement.value;
  if(!query) { return; }

  // Pass query to handler.
  onSearch(query);
}

export default withStyles(styles)(AppBar);
