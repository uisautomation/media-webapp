import React from 'react';
import PropTypes from 'prop-types';

import TextField from '@material-ui/core/TextField';

/**
 * A form which can edit a media item's metadata. Pass the media item resource in the item prop.
 * The onChange prop is called with a patch to the item as it is edited.
 */
const ItemMetadataForm = ({
  item: { title = '', description = '' },
  onChange,
  disabled,
}) => (<div>
  <TextField
    fullWidth
    disabled={ disabled }
    label='Title'
    margin='normal'
    onChange={ event => onChange({ title: event.target.value }) }
    value={ title }
  />

  <TextField
    fullWidth
    disabled={ disabled }
    label='Description'
    margin='normal'
    multiline
    onChange={ event => onChange({ description: event.target.value }) }
    rows={ 4 }
    value={ description }
  />
</div>);

ItemMetadataForm.propTypes = {
  /** Media item resource. */
  item: PropTypes.shape({
    description: PropTypes.string,
    title: PropTypes.string,
  }).isRequired,

  /** Function called when the item changes. Passed a patch style object for the item. */
  onChange: PropTypes.func.isRequired,

  /** Should all the form controls be disabled? */
  disabled: PropTypes.bool,
};

ItemMetadataForm.defaultProps = {
  disabled: false,
};

export default ItemMetadataForm;
