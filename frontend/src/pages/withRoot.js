import React from 'react';
import CssBaseline from '@material-ui/core/CssBaseline';

import ProfileProvider from '../providers/ProfileProvider';
import MathJaxProvider from '../providers/MathJaxProvider';

/**
 * Wrap a component which is intended to be the top-level component for a page
 * so that it can be used as the root component.
 *
 * Put any top-level providers here.
 */
function withRoot(Component) {
  function WithRoot(props) {
    // MuiThemeProvider makes the theme available down the React tree
    // thanks to React context.
    return (
      <MathJaxProvider>
        <ProfileProvider>
          <CssBaseline />
          <Component {...props} />
        </ProfileProvider>
      </MathJaxProvider>
    );
  }

  return WithRoot;
}

export default withRoot;
