import React, { Component } from 'react';

import MuiSnackbar from '@material-ui/core/Snackbar';

const MESSAGE_KEY = 'snackbar_message';

/**
 * Wraps the material-ui Snackbar component and displays a message if it finds one set in
 * localStorage by the exported setMessageForNextPageLoad() method.
 */
class Snackbar extends Component {
  constructor() {
    super();
    this.state = {
      message: null,
      open: false,
    };
  }

  /**
   * Check if a message is stored under MESSAGE_KEY in localStorage. If one is found, delete it
   * and display it in the snackbar.
   */
  componentWillMount() {
    const message = localStorage.getItem(MESSAGE_KEY);
    if (message) {
      localStorage.removeItem(MESSAGE_KEY);
      this.setState({open: true, message: message});
    }
  }

  render() {
    return (
      <MuiSnackbar
        open={this.state.open}
        message={this.state.message}
        autoHideDuration={3000}
        onClose={() => {this.setState({open: false})}}
      />
    );
  }
}

export default Snackbar;

export const setMessageForNextPageLoad = (message) => {
  localStorage.setItem(MESSAGE_KEY, message)
};
