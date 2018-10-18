import * as React from 'react';
import { FetchResources, IPassedProps } from './FetchResources';

import {IMediaListResponse, IMediaQuery, IMediaResource, mediaList} from '../api';

import MediaList from '../components/MediaList';

export interface IProps {
  /** Query to pass to API. */
  query: IMediaQuery;

  /** Component to pass results to. Defaults to MediaList. */
  component: React.ComponentType<IPassedProps<IMediaQuery, IMediaResource>>;

  /** Extra props to pass to the rendered component. */
  componentProps?: {[x: string]: any};

  /** Optional handler that makes the fetched response available to the parent */
  onFetched(response: IMediaListResponse): void;
}

/**
 * A component which fetches a list of list of media items and passes them to a contained
 * component. By default the component is MediaList.
 */
const FetchMediaItems: React.SFC<IProps> = props => (
  <FetchResources fetchResources={ mediaList } {...props} />
);

FetchMediaItems.defaultProps = {
  component: MediaList,
};

export default FetchMediaItems;
