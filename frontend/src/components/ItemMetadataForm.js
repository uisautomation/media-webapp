import React from 'react';
import PropTypes from 'prop-types';

import ChipInput from 'material-ui-chip-input'

import Checkbox from '@material-ui/core/Checkbox';
import FormControlLabel from "@material-ui/core/FormControlLabel";
import TextField from '@material-ui/core/TextField';

import {LANGUAGES_FROM_PAGE} from "../api";
import Autocomplete from "./Autocomplete";
import {withStyles} from "@material-ui/core/styles/index";
import moment from "moment";

const languagesOptionsFromPage = LANGUAGES_FROM_PAGE && LANGUAGES_FROM_PAGE.map(suggestion => ({
  label: suggestion[0] === '' ? '' : suggestion[1],
  value: suggestion[0],
}));

/**
 * A form which can edit a media item's metadata. Pass the media item resource in the item prop.
 * The onChange prop is called with a patch to the item as it is edited.
 */
const ItemMetadataForm = ({
  classes,
  item: { title = '', downloadable, description = '', copyright = '', language, tags, publishedAt },
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


  <ChipInput
    label='Tags'
    value={tags}
    onAdd={(chip) => onChange && onChange({ tags: [ ...tags, chip ] })}
    onDelete={(chip, index) => {
      if (onChange) {
        const copy = [ ...tags ];
        copy.splice(index, 1);
        onChange({ tags: copy });
      }
    }}
  />

  <div className={classes.publishedAt}>
    <TextField
      error={ !!errors.publishedAt }
      helperText={ errors.publishedAt ? errors.publishedAt.join(' ') : null }
      value={publishedAt ? moment(publishedAt).format("YYYY-MM-DD") : ''}
      label="Published At"
      type="date"
      onChange={event => {
        if (onChange) {
          let changedPublishedAt = null;
          if (event.target.value) {
            changedPublishedAt = moment(event.target.value, "YYYY-MM-DD").format();
          }
          onChange({ publishedAt: changedPublishedAt });
        }
      }}
      InputLabelProps={{
        shrink: true,
      }}
    />
  </div>

</div>);

ItemMetadataForm.propTypes = {
  /** Media item resource. */
  item: PropTypes.shape({
    copyright: PropTypes.string,
    description: PropTypes.string,
    downloadable: PropTypes.bool,
    language: PropTypes.string,
    publishedAt: PropTypes.string,
    tags: PropTypes.arrayOf(PropTypes.string),
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
    /** Error messages to show for the publishedAt field. */
    publishedAt: PropTypes.arrayOf(PropTypes.string),
    /** Error messages to show for the title field. */
    title: PropTypes.arrayOf(PropTypes.string),
  }),
};

ItemMetadataForm.defaultProps = {
  disabled: false,
  errors: { },
};

const styles = theme => ({
  publishedAt: {
    margin: [[theme.spacing.unit * 2, 0]]
  },
});

export default withStyles(styles)(ItemMetadataForm);
