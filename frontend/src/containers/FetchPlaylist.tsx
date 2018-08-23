import * as React from 'react';

import { IPlaylistResource, playlistGet } from '../api';

import FetchResource, { IProps } from './FetchResource';

const FetchPlaylist: React.SFC<IProps<IPlaylistResource>> = props => (
  <FetchResource fetchResource={ playlistGet } {...props} />
);

export default FetchPlaylist;
