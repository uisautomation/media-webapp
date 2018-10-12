import React from 'react';
import PropTypes from 'prop-types';

import ResourceList from './ResourceList';

import PlaylistDefaultImage from '../img/playlist-default-image.jpg';

/** A component which renders a list of playlist resources in a grid. */
const PlaylistList = ({ resources, ...otherProps }) => (
  <ResourceList cardProps={ resourcesToProps(resources) } { ...otherProps } />
);

const resourcesToProps = items => (items || []).map(({
  title, description, id
}) => ({
  description,
  href: '/playlists/' + id,
  imageSrc: PlaylistDefaultImage,
  label: 'Playlist',
  title,
}));

export default PlaylistList;
