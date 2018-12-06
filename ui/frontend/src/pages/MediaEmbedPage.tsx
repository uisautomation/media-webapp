import * as React from 'react';

import MediaItemJWPConfigurationProvider from '../providers/MediaItemJWPConfigurationProvider';

import GenericEmbedPage from './GenericEmbedPage';

export interface IProps {
  match: { params: { pk: string; }; };
}

export const MediaEmbedPage = ({ match: { params: { pk } } }: IProps) => (
  <GenericEmbedPage
    id={pk}
    ConfigurationProvider={MediaItemJWPConfigurationProvider}
    errorTitle="This item could not be displayed"
    errorMessage="You may need to sign in to an account with permission to view the content."
  />
);

export default MediaEmbedPage;
