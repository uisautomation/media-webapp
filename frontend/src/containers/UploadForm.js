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
import { mediaCreate, mediaPatch, mediaUploadGet } from '../api';

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
 * Once the user has selected a file *AND* the we have retrieved an upload endpoint, we upload the
 * file. We use XMLHttpRequest to upload the file so that we can give progress information to the
 * user.
 *
 * Once the upload has completed, the publish button is no longer disabled and we "publish" the
 * item by PUT-ing the new metadata via the API.
 */
class UploadForm extends Component {
  constructor() {
    super();

    this.state = {
      // The current *draft* item being edited by the ItemMetadataForm.
      draftItem: { },

      // If non-null, the file selected by the user for upload.
      fileToUpload: null,

      // If non-null, the newly created item.
      item: null,

      // Has the item started to be published?
      publishStarted: false,

      // Did the item upload fail?
      uploadFailed: false,

      // If non-null, a value from 0 to 1 which reflects the current upload progress.
      uploadProgress: null,

      // Did the item upload succeed?
      uploadSucceeded: false,
    };
  }

  render() {
    const { classes } = this.props;
    const {
      draftItem, fileToUpload, publishStarted, uploadProgress, uploadSucceeded
    } = this.state;

    // If the user has not yet selected a file, show the dropzone.
    if(!fileToUpload) {
      return <MediaDropzone
        onDropAccepted={ files => this.setFileToUpload(files[0]) }
      />;
    }

    // Otherwise, show the upload progress and edit form
    return (
      <div>
        <LinearProgress
          variant={ (uploadProgress !== null) ? 'determinate' : 'indeterminate' }
          value={ (uploadProgress !== null) ? 100 * uploadProgress : 0 }
        />

        <ItemMetadataForm
          item={ draftItem }
          disabled={ publishStarted }
          onChange={ patch => this.setState({ draftItem: { ...this.state.draftItem, ...patch } }) }
        />

        <div className={ classes.buttonSet }>
          <Button
            disabled={ !uploadSucceeded || publishStarted }
            color='secondary'
            variant='contained'
            onClick={ () => this.publish() }
          >
            Publish
            {
              uploadSucceeded && !publishStarted
              ?
              <PublishIcon className={ classes.rightIcon } />
              :
              <CircularProgress size={ 24 } className={ classes.rightIcon } />
            }
          </Button>
        </div>
      </div>
    );
  }

  /** Called when the user has selected a file. */
  setFileToUpload(fileToUpload) {
    // Create a new media item and kick off an upload
    const title = fileToUpload.name ? fileToUpload.name : 'Untitled';
    mediaCreate({ title }).then(item => this.setMediaItem(item));
    this.setState({ fileToUpload, draftItem: { title, ...this.state.draftItem } });
  }

  /** Called when a new media item has been created to receive the upload. */
  setMediaItem(item) {
    mediaUploadGet(item).then(({ url }) => this.setUploadUrl(url));
    this.setState({ item, draftItem: { ...item, ...this.state.draftItem } });
  }

  /** Called when a new upload endpoint has been created. */
  setUploadUrl(url) {
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
        this.setState({ uploadProgress: 1, uploadSucceeded: true });
      } else {
        this.setState({ uploadProgress: 1, uploadFailed: true });
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
    this.setState({ uploadProgress: 0, uploadSucceeded: false, uploadFailed: false });
  }

  /** Publishes the draft item by merging it with the new item. */
  publish() {
    const { draftItem, item } = this.state;
    const publishedItem = { ...item, ...draftItem };
    mediaPatch(publishedItem).then(newItem => this.itemPublished(newItem));
    this.setState({ publishStarted: true });
  }

  /** The item was successfully published. */
  itemPublished(item) {
      window.location.href = '/media/' + item.id;
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
