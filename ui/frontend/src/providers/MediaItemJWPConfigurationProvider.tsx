import * as React from 'react';

import { mediaItemJWPConfigurationGet } from '../uiapi';

import GenericJWPConfigurationProvider, { IProps as IGenericProps } from './GenericJWPConfigurationProvider';

// A version of GenericJWPConfigurationProvider's props with the fetchFunction prop removed.
export interface IProps extends Pick<IGenericProps, Exclude<keyof IGenericProps, 'fetchFunction'>> { }

/**
 * A version of GenericJWPConfigurationProvider pre-configured to fetch a media item's
 * configuration.
 */
export const MediaItemJWPConfigurationProvider: React.SFC<IProps> = props => (
  <GenericJWPConfigurationProvider fetchFunction={ mediaItemJWPConfigurationGet } {...props} />
);

export default MediaItemJWPConfigurationProvider;
