import React from 'react';
import PropTypes from 'prop-types';
import ContentLoader from 'react-content-loader';

import { withTheme } from '@material-ui/core/styles';

/**
 * A ``ContentLoader`` placeholder designed to mimic the appearance of a ``MediaItemCard``.
 *
 * Any unknown properties supplied will be spread to the root component.
 */
const MediaItemCardContentLoader = ({ theme, ...otherProps }) => (
  <ContentLoader
    width={300} height={270}
    primaryColor={theme.palette.grey[200]}
    secondaryColor={theme.palette.grey[300]}
    {...otherProps}
  >
    <rect x={0} y={0} rx={4} ry={4} width={300} height={168} />
    <rect x={0} y={184} rx={4} ry={4} width={300} height={24} />
    <rect x={0} y={224} rx={4} ry={4} width={300} height={8} />
    <rect x={0} y={240} rx={4} ry={4} width={300} height={8} />
  </ContentLoader>
);

MediaItemCardContentLoader.propTypes = {
  /** @ignore */
  theme: PropTypes.object.isRequired,
};

export default withTheme()(MediaItemCardContentLoader);
