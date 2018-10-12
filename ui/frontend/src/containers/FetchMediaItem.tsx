import * as React from 'react';

import { IMediaResource, mediaGet } from '../api';

import FetchResource, { IProps } from './FetchResource';

const FetchMediaItem: React.SFC<IProps<IMediaResource>> = props => (
  <FetchResource fetchResource={ mediaGet } {...props} />
);

export default FetchMediaItem;
