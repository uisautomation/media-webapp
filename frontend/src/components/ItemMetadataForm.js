import React from 'react';
import PropTypes from 'prop-types';

import Checkbox from '@material-ui/core/Checkbox';
import FormControlLabel from "@material-ui/core/FormControlLabel";
import TextField from '@material-ui/core/TextField';

import {LANGUAGES_FROM_PAGE} from "../api";
import Autocomplete from "./Autocomplete";

const languagesOptionsFromPage = LANGUAGES_FROM_PAGE && LANGUAGES_FROM_PAGE.map(suggestion => ({
  label: suggestion[0] === '' ? '' : suggestion[1],
  value: suggestion[0],
}));

/**
 * A form which can edit a media item's metadata. Pass the media item resource in the item prop.
 * The onChange prop is called with a patch to the item as it is edited.
 */
const ItemMetadataForm = ({
  item: { title = '', downloadable, description = '', copyright = '', language },
  languageOptions,
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
  />

  <FormControlLabel
    control={
      <Checkbox
        checked={downloadable}
        onChange={ event => onChange && onChange({ downloadable: event.target.checked }) }
      />
    }
    label="Downloadable"
  />

  <Autocomplete
    label='Language'
    options={ languageOptions || languagesOptionsFromPage }
    onChange={ selection => onChange && onChange({ language: selection.value }) }
    defaultValue={ language }
  />

  <TextField
    fullWidth
    error={ !!errors.copyright }
    helperText={ errors.copyright ? errors.copyright.join(' ') : null }
    disabled={ disabled }
    label='Copyright'
    margin='normal'
    onChange={ event => onChange && onChange({ copyright: event.target.value }) }
    value={ copyright }
  />
</div>);

ItemMetadataForm.propTypes = {
  /** Media item resource. */
  item: PropTypes.shape({
    copyright: PropTypes.string,
    description: PropTypes.string,
    downloadable: PropTypes.bool,
    language: PropTypes.string,
    title: PropTypes.string,
  }).isRequired,

  /**
   * A list of language selection options. If not supplied,
   * the component will use LANGUAGES_FROM_PAGE.
   */
  languageOptions: PropTypes.arrayOf(PropTypes.shape({
    label: PropTypes.string,
    value: PropTypes.string,
  })),

  /** Function called when the item changes. Passed a patch style object for the item. */
  onChange: PropTypes.func,

  /** Should all the form controls be disabled? */
  disabled: PropTypes.bool,

  /** A object providing error messages for individual fields of the media item. E.g. if there is
   * an error with the "title" field, add a message to this object under the "title" key.
   */
  errors: PropTypes.shape({
    /** Error messages to show for the copyright field. */
    copyright: PropTypes.arrayOf(PropTypes.string),
    /** Error messages to show for the description field. */
    description: PropTypes.arrayOf(PropTypes.string),
    /** Error messages to show for the title field. */
    title: PropTypes.arrayOf(PropTypes.string),
  }),
};

ItemMetadataForm.defaultProps = {
  disabled: false,
  errors: { },
};

export default ItemMetadataForm;
