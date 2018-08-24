import React from 'react';
import PropTypes from 'prop-types';

import ButtonBase from '@material-ui/core/ButtonBase';
import Grid from '@material-ui/core/Grid';

import { withStyles } from '@material-ui/core/styles';

import MediaItemCard from './MediaItemCard';
import MediaItemCardContentLoader from './MediaItemCardContentLoader';

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

/**
 * A list of channel items within a ``Grid``. Each item is a ``Grid`` item and the root element
 * itself is a ``Grid`` container. Each channel item is a clickable link.
 *
 * Any unknown properties supplied will be spread to the root component.
 */
const ResourceList = withStyles(styles)(({
  classes, defaultItemCount, isLoading, cardProps, GridItemProps, ...otherProps
}) => {
  let resourceComponents;

  if(!isLoading) {
    resourceComponents = (cardProps || []).map(props => (
      <ButtonBase
        classes={{root: classes.buttonRoot}}
        component='a'
        href={props.href}
      >
        <MediaItemCard
          classes={{root: classes.itemRoot}}
          elevation={0}
          {...props}
        />
      </ButtonBase>
    ));
  } else {
    resourceComponents = Array(defaultItemCount).fill(null).map(() => (
      <MediaItemCardContentLoader />
    ));
  }

  return (
    <Grid container spacing={16} {...otherProps}>
      { resourceComponents.map((item, index) => (
        <Grid item xs={12} sm={6} md={4} lg={3} key={index} {...GridItemProps}>{ item }</Grid>
      )) }
    </Grid>
  );
});

ResourceList.propTypes = {
  /** Default number of items to display if content is loading. */
  defaultItemCount: PropTypes.number,

  /** Display defaultItemCount content loading indicators instead of the channel items. */
  isLoading: PropTypes.bool,

  /** Array of MediaItemCard props for items. */
  cardProps: PropTypes.arrayOf(PropTypes.shape({
    description: PropTypes.string,
    href: PropTypes.string,
    imageSrc: PropTypes.string,
    label: PropTypes.string,
    title: PropTypes.string,
  })),
};

ResourceList.defaultProps = {
  GridItemProps: { xs: 12, sm: 6, md: 4, lg: 3, xl: 2 },
  defaultItemCount: 6,
  isLoading: false,
};

export default ResourceList;

