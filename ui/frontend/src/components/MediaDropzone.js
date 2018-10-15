import React from 'react';

import Dropzone from 'react-dropzone';
import { withStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import UploadIcon from '@material-ui/icons/CloudUpload';

/**
 * Display UI encouraging a user to drag and drop media files onto it or to select using the file
 * picker. This is essentially a styled version of [React Dropzone](https://react-dropzone.js.org/)
 * with the accept prop pre-set to ``audio/*, video/*``. See the React Dropzone docs for details on
 * how to use the component.
 */
const MediaDropzone = ({ classes, ...props }) => (
  <Dropzone
    accept='audio/*, video/*'
    className={ classes.root }
    activeClassName={ classes.dragActive }
    acceptClassName={ classes.dragAccept }
    rejectClassName={ classes.dragReject }
    disabledClassName={ classes.disabled }
    style={{}} activeStyle={{}} acceptStyle={{}} rejectStyle={{}} disabledStyle={{}}
    { ...props }
  >
    <UploadIcon className={ classes.uploadIcon }/>
    <Typography gutterBottom color='inherit' variant='title'>Select file to upload</Typography>
    <Typography gutterBottom color='inherit' variant='subheading'>Or drag and drop video files</Typography>
  </Dropzone>
);

const styles = theme => ({
  disabled: {
    border: [['1px', 'solid', theme.palette.action.disabled]],
    color: theme.palette.action.disabled,
  },
  dragAccept: {
    '& $uploadIcon': {
      color: 'green',
    },
  },
  dragReject: {
    '& $uploadIcon': {
      color: 'red',
    },
  },
  root: {
    border: [['1px', 'solid', theme.palette.divider]],
    padding: [[theme.spacing.unit * 3, theme.spacing.unit * 5]],
    textAlign: 'center',
  },
  uploadIcon: {
    fontSize: '10em',
    opacity: 0.25,
  },
});

export default withStyles(styles)(MediaDropzone);
