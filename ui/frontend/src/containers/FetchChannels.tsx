import * as React from 'react';
import { FetchResources, IPassedProps } from './FetchResources';

import { channelList, IChannelQuery, IChannelResource } from '../api';

import ChannelList from '../components/ChannelList';

export interface IProps {
  /** Query to pass to API. */
  query: IChannelQuery;

  /** Component to pass results to. Defaults to ChannelList. */
  component: React.ComponentType<IPassedProps<IChannelQuery, IChannelResource>>;

  /** Extra props to pass to the rendered component. */
  componentProps?: {[x: string]: any};
};

/**
 * A component which fetches a list of list of channel items and passes them to a contained
 * component. By default the component is ChannelList.
 */
const FetchChannelItems: React.SFC<IProps> = props => (
  <FetchResources fetchResources={ channelList } {...props} />
);

FetchChannelItems.defaultProps = {
  component: ChannelList,
};

export default FetchChannelItems;
