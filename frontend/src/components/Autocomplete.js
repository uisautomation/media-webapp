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
  root: {
    flexGrow: 1,
    height: 250,
  },
  input: {
    display: 'flex',
    padding: 0,
  },
  valueContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    flex: 1,
    alignItems: 'center',
  },
  chip: {
    margin: `${theme.spacing.unit / 2}px ${theme.spacing.unit / 4}px`,
  },
  chipFocused: {
    backgroundColor: emphasize(
      theme.palette.type === 'light' ? theme.palette.grey[300] : theme.palette.grey[700],
      0.08,
    ),
  },
  noOptionsMessage: {
    padding: `${theme.spacing.unit}px ${theme.spacing.unit * 2}px`,
  },
  singleValue: {
    fontSize: 16,
  },
  placeholder: {
    position: 'absolute',
    left: 2,
    fontSize: 16,
  },
  paper: {
    position: 'absolute',
    zIndex: 100,
    marginTop: theme.spacing.unit,
    left: 0,
    right: 0,
    height: "900px !important",
  },
  divider: {
    height: theme.spacing.unit * 2,
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
          className: props.selectProps.classes.input,
          inputRef: props.innerRef,
          children: props.children,
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

const loadOptions = options => inputValue => {
      // filter options based on input and only return 20 options
      const filteredOptions = options.filter(option =>
        option.label.toLowerCase().includes(inputValue.toLowerCase())
      ).slice(0, 20);
      // return resolved promise with filtered options
      return new Promise(resolve => resolve(filteredOptions));
};

const Autocomplete = ({ classes, options, value, onChange }) => (
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
    loadOptions={loadOptions(options)}
    placeholder="Language"
    onChange={onChange}
    defaultValue={options.find(option => option.value === value)}
  />
);

Autocomplete.propTypes = {

  /** Error messages to show for the description field. */
  value: PropTypes.arrayOf(PropTypes.string),

  /** Function called when an option is selected. The whole option object is passed. */
  onChange: PropTypes.func,

  /** Should all the form controls be disabled? */
  disabled: PropTypes.bool,

  /** Error messages to show for the title field. */
  title: PropTypes.arrayOf(PropTypes.string),
};

export default withStyles(styles)(Autocomplete);
