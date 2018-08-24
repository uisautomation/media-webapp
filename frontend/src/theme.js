/**
 * Custom University of Cambridge material UI theme
 */

// Since the ordering of properties has some meaning to users editing this file even if they are of
// no interest to the code, we disable the alphabetical sort check.
//
// tslint:disable:object-literal-sort-keys

import { createMuiTheme } from '@material-ui/core/styles';

const defaultTheme = createMuiTheme();

const serifFont = {
  fontFamily: ['"Merriweather"', 'serif'],
};

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
    background: {
      default: '#f3f3f3',
    },
  },
  dimensions: {
    drawerWidth: 30 * 8,
  },
  overrides: {
    MuiTypography: {
      display1: { ...serifFont },
      display2: { ...serifFont },
      display3: { ...serifFont },
      display4: { ...serifFont },
      headline: { ...serifFont },
      title: { ...serifFont },
    },

    MediaItemCard: {
      title: { ...serifFont },
    },
  },
});

export default theme;
