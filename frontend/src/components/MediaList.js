import React from 'react';
import PropTypes from 'prop-types';

import ResourceList from './ResourceList';

/** A component which renders a list of media item resources in a grid. */
const MediaList = ({ resources, ...otherProps }) => (
  <ResourceList cardProps={ resourcesToProps(resources) } { ...otherProps } />
);

const resourcesToProps = items => (items || []).map(({
  title, description, posterImageUrl, id
}) => ({
  description,
  href: '/media/' + id,
  imageSrc: posterImageUrl,
  title,
}));

export default MediaList;
