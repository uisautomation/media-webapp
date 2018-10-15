import React from 'react';
import PropTypes from 'prop-types';

import ResourceList from './ResourceList';

import ChannelDefaultImage from '../img/channel-default-image.jpg';

/** A component which renders a list of channel resources in a grid. */
const ChannelList = ({ resources, ...otherProps }) => (
  <ResourceList cardProps={ resourcesToProps(resources) } { ...otherProps } />
);

const resourcesToProps = items => (items || []).map(({
  title, description, id
}) => ({
  description,
  href: '/channels/' + id,
  imageSrc: ChannelDefaultImage,
  label: 'Channel',
  title,
}));

export default ChannelList;
