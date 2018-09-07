import React, { Component } from 'react';

import PublishIcon from '@material-ui/icons/Publish';

import Button from '@material-ui/core/Button';
import CircularProgress from '@material-ui/core/CircularProgress';
import LinearProgress from '@material-ui/core/LinearProgress';
import Step from '@material-ui/core/Step';
import StepContent from '@material-ui/core/StepContent';
import StepLabel from '@material-ui/core/StepLabel';
import Stepper from '@material-ui/core/Stepper';
import Typography from '@material-ui/core/Typography';

import { withStyles } from '@material-ui/core/styles';

import MediaDropzone from '../components/MediaDropzone';
import ItemMetadataForm from '../components/ItemMetadataForm';
import { mediaCreate, mediaPatch, mediaUploadGet, } from '../api';
import ChannelSelect from "./ChannelSelect";
import * as moment from "moment";

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
      // Active step of the upload process.
      activeStep: 0,

      // Channel to upload to
      channelId: null,

      // The current *draft* item being edited by the ItemMetadataForm.
      // Initialised with sensible defaults.
      draftItem: {
        downloadable: true,
        publishedAt: moment().format()
      },

      // An error object as returned by the API or the empty object if there are no errors.
      errors: { },

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
      activeStep,
      channelId,
      draftItem,
      errors,
      publishStarted,
      uploadProgress,
      uploadSucceeded,
    } = this.state;

    return (
      <Stepper activeStep={ activeStep  } orientation='vertical'>
        <Step>
          <StepLabel>Select channel</StepLabel>
          <StepContent>
            <Typography>
              Select which of your channels this media item should be uploaded to.
            </Typography>
            <ChannelSelect channelId={ channelId } onChange={
              event => this.setState({ channelId: event.target.value, activeStep: 1 })
            } />
          </StepContent>
        </Step>

        <Step>
          <StepLabel>Choose file to upload</StepLabel>
          <StepContent>
            <MediaDropzone
              disabled={ activeStep !== 1}
              onDropAccepted={ files => this.setFileToUpload(files[0]) }
            />
          </StepContent>
        </Step>

        <Step>
          <StepLabel>Edit video metadata</StepLabel>
          <StepContent className={classes.metadata}>
            <ItemMetadataForm
              item={ draftItem }
              errors={ errors }
              disabled={ publishStarted }
              onChange={ patch => this.setState({ draftItem: { ...this.state.draftItem, ...patch } }) }
            />

            <LinearProgress
              variant={ (uploadProgress !== null) ? 'determinate' : 'indeterminate' }
              value={ (uploadProgress !== null) ? 100 * uploadProgress : 0 }
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
                  !uploadSucceeded || publishStarted
                  ?
                  <CircularProgress size={ 24 } className={ classes.rightIcon } />
                  :
                  <PublishIcon className={ classes.rightIcon } />
                }
              </Button>
            </div>
          </StepContent>
        </Step>
      </Stepper>
    );
  }

  /** Called when the user has selected a file. */
  setFileToUpload(fileToUpload) {
    // Create a new media item and kick off an upload
    const title = fileToUpload.name ? fileToUpload.name : 'Untitled';
    const { channelId } = this.state;
    mediaCreate({ title, channelId }).then(item => this.setMediaItem(item));
    this.setState({
      activeStep: 2,
      draftItem: { title, ...this.state.draftItem },
      fileToUpload,
    });
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
    mediaPatch(publishedItem)
      .then(newItem => this.itemPublished(newItem))
      .catch(({ body }) => this.setState({ publishStarted: false, errors: body }));
    this.setState({ publishStarted: true });
  }

  /** The item was successfully published. */
  itemPublished(item) {
      window.location.href = '/media/' + item.id;
  }
}

UploadForm.propTypes = {
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
