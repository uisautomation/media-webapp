import React, { Component } from 'react';
import PropTypes from 'prop-types';

import LinearProgress from '@material-ui/core/LinearProgress';
import CircularProgress from '@material-ui/core/CircularProgress';
import PublishIcon from '@material-ui/icons/Publish';
import Button from '@material-ui/core/Button';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import MediaDropzone from '../components/MediaDropzone';
import ItemMetadataForm from '../components/ItemMetadataForm';
import { mediaPatch } from '../api';

/**
 * A container component which takes a media item resource and upload endpoint via its props and
 * provides the upload flow.
 *
 * This is a somewhat complicated container in that it attempts to make sure that as much
 * interaction is possible, even before the item or upload endpoint resources are available. To
 * that end, it separates the selection of the file from the initiation of the upload. The user can
 * proceed to enter item metadata but can only publish the item when both the original item
 * resource and upload endpoint resource have been set.
 *
 * Once the user has selected a file *AND* the upload endpoint resource is truthy, the upload URL
 * is used to upload the file. We use XMLHttpRequest to upload the file so that we can give
 * progress information to the user.
 *
 * Once the upload has completed and the media item resource is truthy, the publish button is no
 * longer disabled and we "publish" the item but PUT-ing the new metadata via the API.
 */
class UploadForm extends Component {
  constructor(props) {
    super(props);
    this.state = {
      draftItem: { },
      fileToUpload: null,
      publishCompleted: false,
      publishFailed: false,
      publishSucceeded: false,
      publishWasStarted: false,
      publishedItem: null,
      uploadCompleted: false,
      uploadFailed: false,
      uploadProgress: null,  // if non-null, current file upload progress from 0 -> 1
      uploadSucceeded: false,
      uploadWasStarted: false,
    };
  }

  render() {
    const {
      draftItem,
      fileToUpload,
      publishWasStarted,
      uploadProgress,
      uploadSucceeded,
      uploadWasStarted,
    } = this.state;
    const { classes, item, url } = this.props;

    // Initially, just show the upload dropzone
    if(!fileToUpload) {
      return <div>
        <MediaDropzone onDropAccepted={ files => this.receivedFile(files[0]) } />
      </div>;
    }

    // Once we have a file, show upload progress and form.
    return <div>
      <Typography variant='headline'>Update media information</Typography>

      <ItemMetadataForm
        item={ draftItem }
        onChange={ patch => this.patchDraftItem(patch) }
      />

      <LinearProgress
        variant={ uploadWasStarted && (uploadProgress !== null) ? 'determinate' : 'indeterminate' }
        value={ (uploadProgress !== null) ? 100 * uploadProgress : 0 }
      />

      <div className={ classes.buttonSet }>
        {
          publishWasStarted
          ?
          <CircularProgress />
          :
          <Button
            disabled={ !fileToUpload || !uploadSucceeded || !item }
            color='secondary'
            variant='contained'
            onClick={ () => this.publish() }
          >
            Publish
            <PublishIcon className={ classes.rightIcon }/>
          </Button>
        }
      </div>
    </div>;
  }

  componentDidUpdate(prevProps, prevState) {
    const {
      fileToUpload,
      publishCompleted,
      publishSucceeded,
      publishedItem,
      uploadWasStarted,
    } = this.state;
    const { item, url } = this.props;

    // If there was not previously an upload started but we're not in a position to start one, do
    // so. This is not done from receivedFile because when receivedFile is called, we may not yet
    // have received the upload endpoint URL.
    if(!uploadWasStarted && fileToUpload && url) {
      this.startUpload();
      this.patchDraftItem({ name: fileToUpload.name });
    }

    // If the publish started and succeeded, redirect to the media page for the item.
    if(publishedItem && publishCompleted && publishSucceeded) {
      window.location.href = '/media/' + publishedItem.id;
    }
  }

  publish() {
    // Publishes the draft item by merging it with the item we were passed in props
    const { item } = this.props;
    const { draftItem } = this.state;
    const publishedItem = { ...item, ...draftItem };
    mediaPatch(publishedItem)
      .then(() => this.setState({ publishCompleted: true, publishSucceeded: true }))
      .catch(() => this.setState({ publishCompleted: true, publishFailed: true }))
    this.setState({ publishedItem, publishWasStarted: true });
  }

  patchDraftItem(patch) {
    const { draftItem } = this.state;
    this.setState({ draftItem: { ...draftItem, ...patch } });
  }

  receivedFile(file) {
    // Called when a file was selected by the user. Update state to record the new file and reset
    // all the upload state. The upload itself is not started here because the url prop may not yet
    // be set to a useful value. Instead, in componentDidUpdate, we check both the url prop *and*
    // the fileToUpload state and initiate an upload when both are set.

    if(!file) { return; }  // Sanity check arguments

    this.setState({
      fileToUpload: file,
      publishCompleted: false,
      publishFailed: false,
      publishSucceeded: false,
      publishWasStarted: false,
      uploadCompleted: false,
      uploadFailed: false,
      uploadProgress: null,
      uploadSucceeded: false,
      uploadWasStarted: false,
    });
  }

  startUpload() {
    // Start upload. Should be called when the fileToUpload state variable and url prop are
    // populated.

    const { url } = this.props;
    const { fileToUpload } = this.state;

    if(!fileToUpload || !url) { return; } // Sanity check arguments

    // Populate form data object with file to upload
    const formData = new FormData();
    formData.append('file', fileToUpload);

    // Construct a new XMLHttpRequest. We can't use the newer fetch() API because fetch() does not
    // provide progress information.
    const req = new XMLHttpRequest();

    // Function called when loading has finished, for better or worse. Since we don't know quite
    // what subset of XMLHttpRequest the browser supports, we call this both from the
    // readystatechange handler and the load handler so it should be safe to call this multiple
    // times.
    const loadFinished = () => {
      // Examine the status to work out if we succeeded.
      if((req.status >= 200) && (req.status < 300)) {
        this.setState({ uploadProgress: 1, uploadCompleted: true, uploadSucceeded: true });
      } else {
        this.setState({ uploadProgress: 1, uploadCompleted: true, uploadFailed: true });
      }
    };

    // Set up the event handlers for the XMLHttpRequest object.
    req.onreadystatechange = () => { if(req.readyState === 4) { loadFinished(); } };
    req.onload = () => loadFinished();
    req.onprogress = event => {
      if(event.lengthComputable) {
        this.setState({ uploadProgress: event.loaded / event.total });
      } else {
        this.setState({ uploadProgress: null });
      }
    };

    // Actually start the upload.
    req.open('post', url)
    req.send(formData);

    // Record that we started an upload
    this.setState({ uploadCompleted: false, uploadProgress: null, uploadWasStarted: true });
  }
}

UploadForm.propTypes = {
  /** Media item resource which this form will modify. */
  item: PropTypes.object,

  /** Upload endpoint resource which this form uses to upload the selected file. */
  upload: PropTypes.shape({
    url: PropTypes.string,
  }),
};

const styles = theme => ({
  buttonSet: {
    marginTop: theme.spacing.unit,
    textAlign: 'right',
  },
  rightIcon: {
    marginLeft: theme.spacing.unit,
  },
});

export default withStyles(styles)(UploadForm);
