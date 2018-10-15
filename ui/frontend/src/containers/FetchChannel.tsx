import * as React from 'react';

import { channelGet, IChannelResource } from '../api';

import FetchResource, { IProps } from './FetchResource';

const FetchChannel: React.SFC<IProps<IChannelResource>> = props => (
  <FetchResource fetchResource={ channelGet } {...props} />
);

export default FetchChannel;
