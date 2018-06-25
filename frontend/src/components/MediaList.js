import React from 'react';
import PropTypes from 'prop-types';

import ButtonBase from '@material-ui/core/ButtonBase';
import Grid from '@material-ui/core/Grid';

import { withStyles } from '@material-ui/core/styles';

import MediaItemCard from './MediaItemCard';
import MediaItemCardContentLoader from './MediaItemCardContentLoader';

/**
 * A list of media items within a ``Grid``. Each item is a ``Grid`` item and the root element
 * itself is a ``Grid`` container. Each media item is a clickable link.
 *
 * Any unknown properties supplied will be spread to the root component.
 */
const MediaList = ({
  classes, maxItemCount, contentLoading, mediaItems, GridItemProps, ...otherProps
}) => {
  let mediaItemComponents;

  if(!contentLoading) {
    mediaItemComponents = mediaItems.slice(0, maxItemCount).map(item => (
      <ButtonBase
        classes={{root: classes.buttonRoot}}
        component='a'
        href={item.url}
      >
        <MediaItemCard
          classes={{root: classes.itemRoot}}
          title={item.title}
          description={item.description}
          imageSrc={item.imageUrl}
          label={item.label}
          elevation={0}
        />
      </ButtonBase>
    ));
  } else {
    mediaItemComponents = Array(maxItemCount || 6).fill(null).map(() => (
      <MediaItemCardContentLoader />
    ));
  }

  return (
    <Grid container spacing={16} {...otherProps}>
      { mediaItemComponents.map((item, index) => (
        <Grid item xs={12} sm={6} md={4} lg={3} key={index} {...GridItemProps}>{ item }</Grid>
      )) }
    </Grid>
  );
}

MediaList.propTypes = {
  /** @ignore */
  classes: PropTypes.object.isRequired,

  /** Maximum item count to display. If unset, all items will be displayed. */
  maxItemCount: PropTypes.number,

  /** Display maxItemCount content loading indicators instead of the media items. */
  contentLoading: PropTypes.bool,

  /** Array of media items to show. */
  mediaItems: PropTypes.arrayOf(PropTypes.shape({
    /** URL representing media item used as link target. */
    url: PropTypes.string.isRequired,

    /** Title of media item. */
    title: PropTypes.string.isRequired,

    /** Description of media item. */
    description: PropTypes.string,

    /** URL of image representing media item. */
    imageUrl: PropTypes.string.isRequired,

    /** Some label used to indicate media item is special in some way. */
    label: PropTypes.string,
  })),
};

MediaList.defaultProps = {
  GridItemProps: { xs: 4 },
  contentLoading: false,
  mediaItems: [],
};

const styles = theme => ({
  buttonRoot: {
    '&:hover': {
      '&::after': {
        backgroundColor: theme.palette.action.hover,
        content: "''",
        display: 'block',
        height: '100%',
        left: 0,
        position: 'absolute',
        top: 0,
        width: '100%',
      },
      boxShadow: theme.shadows[6],
    },
    boxShadow: theme.shadows[2],
    padding: 0,
    position: 'relative',
    textAlign: 'inherit',
    transition: [
      theme.transitions.create('box-shadow'),
      theme.transitions.create('background-color'),
    ],
    width: '100%',
  },

  itemRoot: {
    width: '100%',
  },

  root: {
    backgroundColor: theme.palette.background.paper,
    display: 'flex',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    overflow: 'hidden',
  },
});

export default withStyles(styles)(MediaList);
