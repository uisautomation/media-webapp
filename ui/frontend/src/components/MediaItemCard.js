import React from 'react';
import PropTypes from 'prop-types';

import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import CardMedia from '@material-ui/core/CardMedia';
import Typography from '@material-ui/core/Typography';

import { withStyles } from '@material-ui/core/styles';

/**
 * A ``Card`` representing a particular media item.
 *
 * Any unknown properties supplied will be spread to the root component.
 */
const MediaItemCard = ({ title, description, imageSrc, label, classes, ...otherProps }) => (
  <Card className={classes.root} {...otherProps}>
    <CardMedia className={classes.media} image={imageSrc} />
    <CardContent className={classes.content}>
      <Typography gutterBottom variant="body2" component="h2" className={classes.title}>
        { title }
      </Typography>
      <Typography variant="caption" component="p" className={classes.description}>
        <span className={classes.descriptionContent}>
          { description }
          <span className={classes.descriptionEllipsis}>&nbsp;</span>
        </span>
      </Typography>
    </CardContent>
    {
      label
        ? <Typography variant="body1" classes={{ root: classes.label }}>
          { label }
        </Typography>
        : null
    }
  </Card>
);

MediaItemCard.propTypes = {
  /** @ignore */
  classes: PropTypes.object.isRequired,

  /** Title of the media item. */
  title: PropTypes.string.isRequired,

  /** URL for an image representing the media item. */
  imageSrc: PropTypes.string.isRequired,

  /** Description of the media item. */
  description: PropTypes.string,

  /** A label for the item indicating it has some special property. */
  label: PropTypes.string,
};

const styles = theme => ({
  root: {
    position: 'relative',
  },

  media: {
    height: 0,
    paddingTop: '56.25%', // 16:9
  },

  label: {
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    borderBottomRightRadius: theme.spacing.unit * 0.25,
    color: 'white',
    left: 0,
    padding: theme.spacing.unit,
    position: 'absolute',
    textTransform: 'uppercase',
    top: 0,
  },

  title: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },

  description: {
    display: 'block',
    overflow: 'hidden',
    position: 'relative',
  },
  descriptionContent: {
    display: 'block',
    height: '4em',
    position: 'relative',
  },
  descriptionEllipsis: {
    background: 'linear-gradient(to bottom, rgba(255,255,255,0), ' + theme.palette.background.paper + ')',
    height: '2em',
    position: 'absolute',
    right: 0,
    top: '2em',
    width: '100%',
  },
});

export default withStyles(styles, { name: 'MediaItemCard' })(MediaItemCard);
