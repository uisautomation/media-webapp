import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import MuiSnackbar from '@material-ui/core/Snackbar';
import IconButton from '@material-ui/core/IconButton';
import CloseIcon from '@material-ui/icons/Close';

// A global callback which can be used to set the snackbar message.
//
// This is a little bit of a HACK based on the approach in [1]. Really this should be flux-y rather
// than callback-y but it's not worth the overhead of selecting and adding some flux implementation
// just for the snackbar at the moment. If we have some other global state in the frontend, we
// should migrate this to whatever flux implementation we end up using.
//
// [1] https://medium.freecodecamp.org/how-to-show-informational-messages-using-material-ui-in-a-react-web-app-5b108178608
let globalShowMessageFunc = null;

// The snackbar implementation itself is based on the "Consecutive Snackbars" example from the
// Material UI docs [2].
//
// [2] https://material-ui.com/demos/snackbars/

const styles = theme => ({
  close: {
    padding: theme.spacing.unit / 2,
  },
});

class Snackbar extends React.Component {
  queue = [];

  state = {
    messageInfo: {},
    open: false,
  };

  componentDidMount() {
    // When the component mounts, update the global showMessageHandler variable. In essence this
    // means that the last mounted snackbar components "wins" the right to show future messages.
    globalShowMessageFunc = this.showMessage;
  }

  componentWillUnmount() {
    // If the current showMessageHandler is our one, unset it to prevent callers to the global
    // showMessage() function calling a handler after we've unmounted.
    if(globalShowMessageFunc === this.showMessage) { globalShowMessageFunc = null; }
  }

  showMessage = message => {
    this.queue.push({
      key: new Date().getTime(),
      message,
    });

    if (this.state.open) {
      // immediately begin dismissing current message
      // to start showing new one
      this.setState({ open: false });
    } else {
      this.processQueue();
    }
  };

  processQueue = () => {
    if (this.queue.length > 0) {
      this.setState({
        messageInfo: this.queue.shift(),
        open: true,
      });
    }
  };

  handleClose = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    this.setState({ open: false });
  };

  handleExited = () => {
    this.processQueue();
  };

  render() {
    const { classes } = this.props;
    const { message, key } = this.state.messageInfo;
    return (
      <MuiSnackbar
        key={key}
        anchorOrigin={{
          horizontal: 'left',
          vertical: 'bottom',
        }}
        open={this.state.open}
        autoHideDuration={3000}
        onClose={this.handleClose}
        onExited={this.handleExited}
        ContentProps={{
          'aria-describedby': 'message-id',
        }}
        message={<span id="message-id">{message}</span>}
        action={[
          <IconButton
            key="close"
            aria-label="Close"
            color="inherit"
            className={classes.close}
            onClick={this.handleClose}
          >
            <CloseIcon />
          </IconButton>,
        ]}
      />
    );
  }
}

Snackbar.propTypes = {
  classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(Snackbar);

/**
 * Show a message to the user.
 */
export const showMessage = message => {
  // We would normally show an error to the user if there is no handler but since this is our "show
  // message to the user" code path, we can't really do anything other than drop the message :S.
  if(!globalShowMessageFunc) {
    // tslint:disable-next-line:no-console
    console.error('globalShowMessageFunc is undefined');
    return;
  }

  globalShowMessageFunc(message);
}
