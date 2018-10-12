import React from 'react';
import PropTypes from 'prop-types';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import Button from '@material-ui/core/Button';

/**
 * A modal dialogue box that asks for confirmation before deleting a playlist.
 */
const DeletePlaylistDialog = ({ title, isOpen, handleConfirmDelete }) => (
  <Dialog open={isOpen}>
    <DialogTitle>Delete Playlist Permanently?</DialogTitle>
    <DialogContent>
      <DialogContentText>
        Once deleted, the playlist <strong>"{ title }"</strong> cannot be recovered.
        None of the playlist's media items will be deleted.
      </DialogContentText>
    </DialogContent>
    <DialogActions>
      <Button color="primary" onClick={() => handleConfirmDelete(false)}>
        Cancel
      </Button>
      <Button color="primary" onClick={() => handleConfirmDelete(true)}>
        Delete
      </Button>
    </DialogActions>
  </Dialog>
);

DeletePlaylistDialog.propTypes = {
  handleConfirmDelete: PropTypes.func.isRequired,
  isOpen: PropTypes.bool.isRequired,
  title: PropTypes.string.isRequired,
};

export default DeletePlaylistDialog
