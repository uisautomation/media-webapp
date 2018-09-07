import React from 'react';
import PropTypes from 'prop-types';

import AsyncSelect from 'react-select/lib/Async';

import { emphasize } from '@material-ui/core/styles/colorManipulator';
import { withStyles } from '@material-ui/core/styles';
import MenuItem from "@material-ui/core/MenuItem";
import Paper from "@material-ui/core/Paper";
import TextField from '@material-ui/core/TextField';
import Typography from '@material-ui/core/Typography';

const styles = theme => ({
  chip: {
    margin: `${theme.spacing.unit / 2}px ${theme.spacing.unit / 4}px`,
  },
  chipFocused: {
    backgroundColor: emphasize(
      theme.palette.type === 'light' ? theme.palette.grey[300] : theme.palette.grey[700],
      0.08,
    ),
  },
  divider: {
    height: theme.spacing.unit * 2,
  },
  input: {
    display: 'flex',
    padding: 0,
  },
  noOptionsMessage: {
    padding: `${theme.spacing.unit}px ${theme.spacing.unit * 2}px`,
  },
  paper: {
    left: 0,
    marginTop: theme.spacing.unit,
    position: 'absolute',
    right: 0,
    zIndex: 10,

  },
  placeholder: {
    fontSize: 16,
    left: 2,
    position: 'absolute',
  },
  root: {
    flexGrow: 1,
    height: 250,
  },
  singleValue: {
    fontSize: 16,
  },
  valueContainer: {
    alignItems: 'center',
    display: 'flex',
    flex: 1,
    flexWrap: 'wrap',
  },
});

function NoOptionsMessage(props) {
  return (
    <Typography
      color="textSecondary"
      className={props.selectProps.classes.noOptionsMessage}
      {...props.innerProps}
    >
      {props.children}
    </Typography>
  );
}

function inputComponent({ inputRef, ...props }) {
  return <div ref={inputRef} {...props} />;
}

function Control(props) {
  return (
    <TextField
      fullWidth
      InputProps={{
        inputComponent,
        inputProps: {
          children: props.children,
          className: props.selectProps.classes.input,
          inputRef: props.innerRef,
          ...props.innerProps,
        },
      }}
      {...props.selectProps.textFieldProps}
    />
  );
}

function Option(props) {
  return (
    <MenuItem
      buttonRef={props.innerRef}
      selected={props.isFocused}
      component="div"
      style={{
        fontWeight: props.isSelected ? 500 : 400,
      }}
      {...props.innerProps}
    >
      {props.children}
    </MenuItem>
  );
}

function Placeholder(props) {
  return (
    <Typography
      color="textSecondary"
      className={props.selectProps.classes.placeholder}
      {...props.innerProps}
    >
      {props.children}
    </Typography>
  );
}

function SingleValue(props) {
  return (
    <Typography className={props.selectProps.classes.singleValue} {...props.innerProps}>
      {props.children}
    </Typography>
  );
}

function ValueContainer(props) {
  return <div className={props.selectProps.classes.valueContainer}>{props.children}</div>;
}

function Menu(props) {
  return (
    <Paper square className={props.selectProps.classes.paper} {...props.innerProps}>
      {props.children}
    </Paper>
  );
}

const loadOptions = (options, inputValue) => {
      // filter options based on input and only return 20 options
      const filteredOptions = options.filter(option =>
        option.label.toLowerCase().includes(inputValue.toLowerCase())
      ).slice(0, 20);
      // return resolved promise with filtered options
      return new Promise(resolve => resolve(filteredOptions));
};

/**
 * A form input select component that offers typical auto-completion behaviour for a large set of
 * options. The component closely follows the
 * [Material UI Autocomplete example](https://material-ui.com/demos/autocomplete) using the
 * `react-select` library. The `AsyncSelect` component was used in favour of the basic `Select`
 * component as the later was unable to handle very large lists of options efficiently.
 */
const Autocomplete = ({ classes, label, placeholder, options, defaultValue, onChange }) => (
  <AsyncSelect
    cacheOptions
    defaultOptions
    classes={classes}
    components={{
      Control,
      Menu,
      NoOptionsMessage,
      Option,
      Placeholder,
      SingleValue,
      ValueContainer,
    }}
    textFieldProps={{
      InputLabelProps: {
        shrink: true,
      },
      label: label,
    }}
    loadOptions={inputValue => loadOptions(options || [], inputValue)}
    onChange={onChange}
    defaultValue={options && options.find(option => option.value === defaultValue)}
    placeholder={placeholder}
  />
);

Autocomplete.propTypes = {

  /** The default to display as selected. */
  defaultValue: PropTypes.string,

  /** The text field's label. */
  label: PropTypes.string,

  /** Function called when an option is selected. The whole option object is passed. */
  onChange: PropTypes.func,

  /** A list of selection options. */
  options: PropTypes.arrayOf(PropTypes.shape({
    label: PropTypes.string,
    value: PropTypes.string,
  })),

  /** The text field's placeholder. */
  placeholder: PropTypes.string,
};

export default withStyles(styles)(Autocomplete);
