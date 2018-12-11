import * as React from 'react';

import { playlistJWPConfigurationGet } from '../uiapi';

import GenericJWPConfigurationProvider, { IProps as IGenericProps } from './GenericJWPConfigurationProvider';

// A version of GenericJWPConfigurationProvider's props with the fetchFunction prop removed.
export interface IProps extends Pick<IGenericProps, Exclude<keyof IGenericProps, 'fetchFunction'>> { }

/**
 * A version of GenericJWPConfigurationProvider pre-configured to fetch a playlist's configuration.
 */
export const PlaylistJWPConfigurationProvider: React.SFC<IProps> = props => (
  <GenericJWPConfigurationProvider fetchFunction={ playlistJWPConfigurationGet } {...props} />
);

export default PlaylistJWPConfigurationProvider;
