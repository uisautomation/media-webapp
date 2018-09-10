import React from 'react';
import PropTypes from 'prop-types';

import moment from "moment";
import ChipInput from 'material-ui-chip-input'

import Checkbox from '@material-ui/core/Checkbox';
import FormControlLabel from "@material-ui/core/FormControlLabel";
import Grid from "@material-ui/core/Grid";
import TextField from '@material-ui/core/TextField';

import {withStyles} from "@material-ui/core/styles/index";

import LANGUAGES_FROM_PAGE from "../data/iso-631-languages.json";
import Autocomplete from "./Autocomplete";

const languagesOptionsFromPage = LANGUAGES_FROM_PAGE.map(suggestion => ({
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
    placeholder='Enter a title, eg. Boundary Singularities'
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
    placeholder='Enter a description (markdown can be used)'
    margin='normal'
    multiline
    onChange={ event => onChange && onChange({ description: event.target.value }) }
    rows={ 4 }
    value={ description }
    InputLabelProps={ { shrink: true } }
  />

  <FormControlLabel
    checked={downloadable}
    onChange={ event => onChange && onChange({ downloadable: event.target.checked }) }
    control={
      <Checkbox
      />
    }
    label="Allow media to be downloaded and indexed by search engines"
  />

  <Grid container spacing={8}>
    <Grid item xs={12} sm={6}>
      <TextField
        className={classes.publishedAt}
        fullWidth
        error={ !!errors.publishedAt }
        helperText={ errors.publishedAt ? errors.publishedAt.join(' ') : null }
        value={publishedAt ? moment(publishedAt).format("YYYY-MM-DD") : ''}
        label="When the item will be published"
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
        InputLabelProps={ { shrink: true } }
      />
    </Grid>
    <Grid item xs={12} sm={6} className={classes.languageContainer}>
      <Autocomplete
        label='Language'
        options={ languagesOptionsFromPage }
        onChange={ selection => onChange && onChange({ language: selection.value }) }
        defaultValue={ language }
        placeholder="Select a language, eg. English"
      />
    </Grid>
  </Grid>

  <TextField
    fullWidth
    error={ !!errors.copyright }
    helperText={ errors.copyright ? errors.copyright.join(' ') : null }
    disabled={ disabled }
    label='Copyright'
    margin='normal'
    onChange={ event => onChange && onChange({ copyright: event.target.value }) }
    value={ copyright }
    placeholder="Enter the copyright, eg. Peterhouse"
    InputLabelProps={ { shrink: true } }
  />

  <ChipInput
    className={classes.tags}
    fullWidth
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
    placeholder="Enter text tags, eg. Einstein, Christmas, Livestock"
    InputLabelProps={ { shrink: true } }
  />

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
  tags: {
    '& input': {
      width: 300
    },
    marginTop: theme.spacing.unit * 3
  },
  languageContainer: {
    marginTop: 12
  }
});

export default withStyles(styles)(ItemMetadataForm);
