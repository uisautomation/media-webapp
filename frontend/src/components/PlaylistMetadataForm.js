import React from 'react';
import PropTypes from 'prop-types';

import TextField from '@material-ui/core/TextField';

/**
 * A form which can edit a playlist's metadata. Pass the playlist resource in the playlist prop.
 * The onChange prop is called with a patch to the playlist as it is edited.
 */
const PlaylistMetadataForm = ({
  playlist: { title = '', description = '' },
  onChange,
  disabled,
  errors,
}) => (<div>
  <TextField
    fullWidth
    error={ !!errors.title }
    helperText={ errors.title ? errors.title.join(' ') : null }
    disabled={ disabled }
    label='Title'
    margin='normal'
    onChange={ event => onChange && onChange({ title: event.target.value }) }
    value={ title }
    InputLabelProps={ { shrink: true } }
  />

  <TextField
    fullWidth
    error={ !!errors.description }
    helperText={ errors.description ? errors.description.join(' ') : null }
    disabled={ disabled }
    label='Description'
    margin='normal'
    multiline
    onChange={ event => onChange && onChange({ description: event.target.value }) }
    rows={ 4 }
    value={ description }
    InputLabelProps={ { shrink: true } }
  />
</div>);

PlaylistMetadataForm.propTypes = {
  /** Playlist resource. */
  playlist: PropTypes.shape({
    description: PropTypes.string,
    title: PropTypes.string,
  }).isRequired,

  /** Function called when the playlist changes. Passed a patch style object for the playlist. */
  onChange: PropTypes.func,

  /** Should all the form controls be disabled? */
  disabled: PropTypes.bool,

  /**
   * A object providing error messages for individual fields of the playlist. E.g. if there is
   * an error with the "title" field, add a message to this object under the "title" key.
   */
  errors: PropTypes.shape({
    /** Error messages to show for the description field. */
    description: PropTypes.arrayOf(PropTypes.string),

    /** Error messages to show for the title field. */
    title: PropTypes.arrayOf(PropTypes.string),
  }),
};

PlaylistMetadataForm.defaultProps = {
  disabled: false,
  errors: { },
};

export default PlaylistMetadataForm;
