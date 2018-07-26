import React from 'react';
import PropTypes from 'prop-types';

import TextField from '@material-ui/core/TextField';

/**
 * A form which can edit a media item's metadata. Pass the media item resource in the item prop.
 * The onChange prop is called with a patch to the item as it is edited.
 */
const ItemMetadataForm = ({
  item: { name = '', description = '' },
  onChange,
}) => (<div>
  <TextField
    fullWidth
    label='Title'
    margin='normal'
    onChange={ event => onChange({ name: event.target.value }) }
    value={ name }
  />

  <TextField
    fullWidth
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
    name: PropTypes.string,
  }).isRequired,

  /** Function called when the item changes. Passed a patch style object for the item. */
  onChange: PropTypes.func.isRequired,
};

export default ItemMetadataForm;
