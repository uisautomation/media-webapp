import React, { Component } from 'react';
import PropTypes from 'prop-types';

import MuiAppBar from '@material-ui/core/AppBar';
import Hidden from '@material-ui/core/Hidden';
import IconButton from '@material-ui/core/IconButton';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import BackIcon from '@material-ui/icons/ArrowBack';
import MenuIcon from '@material-ui/icons/Menu';
import SearchIcon from '@material-ui/icons/Search';
import SearchForm from './SearchForm';

import LogoImage from '../img/logo.svg';

// The location for a redirected search request
// TODO this is to be refactored as per https://github.com/uisautomation/sms-webapp/issues/102
const SEARCH_LOCATION = '/';

/**
 * AppBar component for the media service. Children appear in the right-most part of the bar for
 * larger screen sizes.
 *
 * Any unknown properties supplied will be spread to the root component.
 */
class AppBar extends Component {
  constructor() {
    super();
    this.state = { searchBarVisible: false };
  }

  render() {
    const {
      classes, defaultSearch, onSearch, color, children, autoFocus, onMenuClick, ...otherProps
    } = this.props;
    const { searchBarVisible } = this.state;

    const searchForm = (
      <SearchForm
        autoFocus={autoFocus}
        color={color}
        classes={{
          root: classes.searchFormRoot,
          searchButtonRoot: classes.searchFormButtonRoot,
          searchInputInput: classes.searchFormInputInput,
          searchInputRoot: classes.searchFormInputRoot,
        }}
        onSubmit={
          event => { this.setState({ searchBarVisible: false }); handleSubmit(event, onSearch); }
        }
        InputProps={{
          defaultValue: defaultSearch,
          name: 'q',
          placeholder: 'Search',
        }}
      />
    );

    const toolBar = (
      searchBarVisible
      ?
      <Toolbar>
        <IconButton
          color="inherit" aria-label="Back" className={ classes.leftButton }
          onClick={ () => this.setState({ searchBarVisible: false }) }
        >
          <BackIcon />
        </IconButton>
        { searchForm }
      </Toolbar>
      :
      <Toolbar>
          <Hidden mdUp implementation="css">
            <IconButton
              color="inherit"
              aria-label="Open drawer"
              className={ classes.leftButton }
              onClick={ () => onMenuClick && onMenuClick() }
            >
              <MenuIcon />
            </IconButton>
          </Hidden>
          <Typography variant="title" color="inherit">
            <a href='/'>
              <img src={LogoImage} alt="Media Platform" style={{verticalAlign: 'bottom', height: '1.8em'}} />
            </a>
          </Typography>
          <div className={ classes.centreSection }>
            <div className={ classes.searchFormContainer }>{ searchForm }</div>
          </div>
          <IconButton
            color="inherit" aria-label="Search" className={ classes.searchButton }
            onClick={ () => this.setState({ searchBarVisible: true }) }
          >
            <SearchIcon />
          </IconButton>
          { children }
      </Toolbar>
    );

    return (
      <MuiAppBar position="static" color={color} className={classes.root} {...otherProps}>
        { toolBar }
      </MuiAppBar>
    );
  }
}

AppBar.propTypes = {
  /** If true, the search form input will be focussed. */
  autoFocus: PropTypes.bool,

  /** The color of the component. */
  color: PropTypes.oneOf(['default', 'inherit', 'primary', 'secondary']),

  /** Default search text to populate the search form with. */
  defaultSearch: PropTypes.string,

  /** Function called with search text. If not provided, the submit redirects with the search
   * params: ``?q={text}``
   */
  onSearch: PropTypes.func,

  /** Function called when the navigation menu toggle button is clicked. */
  onMenuClick: PropTypes.func,
};

AppBar.defaultProps = {
  autoFocus: true,
  color: 'primary'
};

const handleSubmit = (event, onSearch) => {
  // Prevent default handling of submit event.
  event.preventDefault();

  // Get value from input element.
  const formElement = event.target;
  const inputElement = Array.from(formElement.elements).filter(element => element.name === 'q')[0];
  if(!inputElement) { return; }

  // Get query from input element.
  const query = inputElement.value;
  if(!query) { return; }

  if(onSearch) {
    // Pass query to handler.
    onSearch(query);
  } else {
    // no search handler so redirect the search
    location = SEARCH_LOCATION + '?q=' + encodeURI(query);
  }
};

const styles = theme => ({
  root: { /* no default styles */ },

  centreSection: {
    display: 'flex',
    flexGrow: 1,
    justifyContent: 'center',
  },

  leftButton: {
    marginLeft: -1.5 * theme.spacing.unit,
    marginRight: 1.5 * theme.spacing.unit,
  },

  searchButton: {
    [theme.breakpoints.up('md')]: {
      display: 'none',
    },
  },

  searchFormContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginLeft: theme.spacing.unit * 2,
    maxWidth: theme.spacing.unit * 80,
    width: '100%',

    [theme.breakpoints.down('sm')]: {
      display: 'none',
    },
  },

  searchFormRoot: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    border: 'none',
    width: '100%',
  },

  searchFormInputInput: {
    width: '100%',
  },

  searchFormButtonRoot: {
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    color: theme.palette.common.white,
  },

  searchFormInputRoot: {
    color: theme.palette.common.white,
    width: '100%',
  },
});

export default withStyles(styles)(AppBar);
