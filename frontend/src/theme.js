/**
 * Custom University of Cambridge material UI theme
 */

// Since the ordering of properties has some meaning to users editing this file even if they are of
// no interest to the code, we disable the alphabetical sort check.
//
// tslint:disable:object-literal-sort-keys

import { createMuiTheme } from '@material-ui/core/styles';

const defaultTheme = createMuiTheme();

const theme = createMuiTheme({
  // This palette was designed using the material palette design tool and University style
  // guidelines:
  // https://material.io/tools/color/#!/?view.left=1&view.right=1&secondary.color=EA7125&primary.color=0072CF
  // https://www.cam.ac.uk/brand-resources/guidelines/typography-and-colour/rgb-and-websafe-references
  palette: {
    primary: {
      light: '#5da0ff',
      main: '#0072cf',
      dark: '#00489d',
      contrastText: '#fff',
    },
    secondary: {
      light: '#ffef79',
      main: '#f3bd48',
      dark: '#bd8d0f',
      contrastText: '#000',
    },
  },
  dimensions: {
    drawerWidth: 30 * 8,
  },
  mixins: {
    // A section of the body of the page which has the left and right padding set to match the
    // padding of the app bar. This padding depends on screen size.
    bodySection: {
      paddingLeft: defaultTheme.spacing.unit * 2,
      paddingRight: defaultTheme.spacing.unit * 2,

      [defaultTheme.breakpoints.up('sm')]: {
        paddingLeft: defaultTheme.spacing.unit * 3,
        paddingRight: defaultTheme.spacing.unit * 3,
      },
    },
  },
});

export default theme;
