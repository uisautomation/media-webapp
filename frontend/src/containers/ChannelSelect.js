import React from 'react';

import FormControl from '@material-ui/core/FormControl';
import FormHelperText from '@material-ui/core/FormHelperText';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import Select from '@material-ui/core/Select';

import {withProfile} from "../providers/ProfileProvider";

/**
 * An input component for the selection of a channel.
 * TODO could be made to pre-select if there is exactly one channel.
 */
const ChannelSelect = ({
  profile, errors, channelId, onChange
}) => {
  const channels = profile ? profile.channels : [];
  return (
    <FormControl fullWidth error={ !!errors }>
      <InputLabel htmlFor="channelId">Channel</InputLabel>
      <Select
        value={ channelId ? channelId : '' }
        onChange={ onChange }
        inputProps={ {id: 'channelId'} }
      >
        {
          channels.map(channel => (
            <MenuItem key={ channel.id } value={ channel.id }>
              { channel.title }
            </MenuItem>
          ))
        }
      </Select>
      <FormHelperText>{ errors ? errors.join(' ') : null }</FormHelperText>
    </FormControl>
  )
};

export default withProfile(ChannelSelect);
