import * as React from 'react';
import { FetchResources, IPassedProps } from './FetchResources';

import { IPlaylistQuery, IPlaylistResource, playlistList } from '../api';

import PlaylistList from '../components/PlaylistList';

export interface IProps {
  /** Query to pass to API. */
  query: IPlaylistQuery;

  /** Component to pass results to. Defaults to PlaylistList. */
  component: React.ComponentType<IPassedProps<IPlaylistQuery, IPlaylistResource>>;

  /** Extra props to pass to the rendered component. */
  componentProps?: {[x: string]: any};
};

/**
 * A component which fetches a list of list of playlist items and passes them to a contained
 * component. By default the component is PlaylistList.
 */
const FetchPlaylistItems: React.SFC<IProps> = props => (
  <FetchResources fetchResources={ playlistList } {...props} />
);

FetchPlaylistItems.defaultProps = {
  component: PlaylistList,
};

export default FetchPlaylistItems;
