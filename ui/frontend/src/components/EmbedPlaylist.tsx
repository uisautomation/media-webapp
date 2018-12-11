// Embedded playlist components.
//
// These components are designed to be used in the embed page for a playlist. They work together.
// As an example:
//
//  <EmbedPlaylist>
//    <EmbedPlaylistItem>
//      <EmbedPlaylistImage url="http://example.invalid/1" />
//      <EmbedPlaylistCaption title="some title" />
//    </EmbedPlaylistItem>
//    <EmbedPlaylistItem>
//      <EmbedPlaylistImage url="http://example.invalid/2" />
//      <EmbedPlaylistCaption title="another title" />
//    </EmbedPlaylistItem>
//  </EmbedPlaylist>
//
// Under the covers they are based on ul and li tags but are heavily styled.
//
import * as React from 'react';

import classNames from 'classnames';

import { createStyles, Theme, withStyles, WithStyles } from '@material-ui/core/styles';

import ButtonBase, { ButtonBaseProps } from '@material-ui/core/ButtonBase';
import Typography from '@material-ui/core/Typography';

const embedPlaylistStyles = (theme: Theme) => createStyles({
  root: {
    margin: 0,
    padding: 0,

    alignItems: 'stretch',
    display: 'flex',
    flexDirection: 'column',
  }
});

export interface IEmbedPlaylistProps extends WithStyles<typeof embedPlaylistStyles> {
  children?: React.ReactNode;
};

export const EmbedPlaylist = withStyles(embedPlaylistStyles)((
  { classes, children }: IEmbedPlaylistProps
) => (
  <ul className={ classes.root }>
    { children }
  </ul>
));

const embedPlaylistItemStyles = (theme: Theme) => createStyles({
  root: {
    margin: 0,
    minHeight: theme.spacing.unit * 11,
    padding: 0,
    width: '100%',
  },

  innerWrapper: {
    alignItems: 'flex-start',
    display: 'flex',
    textAlign: 'left',

    padding: theme.spacing.unit * 2,
    width: '100%',

    '&:hover': {
      backgroundColor: 'rgba(255, 255, 255, 0.08)',
    },
  },

  selected: {
    backgroundColor: theme.palette.primary.dark,
  },
});

export interface IEmbedPlaylistItemProps extends WithStyles<typeof embedPlaylistItemStyles> {
  ButtonProps?: ButtonBaseProps;

  children?: React.ReactNode;

  onClick?: ButtonBaseProps['onClick'];

  selected?: boolean;
};

export const EmbedPlaylistItem = withStyles(embedPlaylistItemStyles)((
  { classes, children, onClick, ButtonProps, selected }: IEmbedPlaylistItemProps
) => (
  <ButtonBase
    component='li' onClick={ onClick }
    className={ classNames(classes.root, {[classes.selected]: selected}) }
    {...ButtonProps}
  >
    <div className={ classes.innerWrapper }>
      { children }
    </div>
  </ButtonBase>
));

EmbedPlaylistItem.defaultProps = {
  selected: false,
}

const embedPlaylistImageStyles = (theme: Theme) => createStyles({
  root: {
    backgroundPosition: 'center',
    backgroundSize: 'cover',
    height: theme.spacing.unit * 7,
    marginRight: theme.spacing.unit * 2,
    minWidth: theme.spacing.unit * 12,
    width: theme.spacing.unit * 12,
  },

  selected: {
    boxShadow: `inset 0 0 0 2px ${theme.palette.primary.light}`,
  }
});

export interface IEmbedPlaylistImageProps extends WithStyles<typeof embedPlaylistImageStyles> {
  url: string;

  selected?: boolean;
}

export const EmbedPlaylistImage = withStyles(embedPlaylistImageStyles)((
  { selected, classes, url }: IEmbedPlaylistImageProps
) => (
  // We replace the background image with CSS here to make sure the background-size property is
  // applied.
  <div
    className={ classNames(classes.root, {[classes.selected]: selected}) }
    style={{ backgroundImage: `url(${url})` }}>
    { /* Add an img tag to aid accessibility */ }
    <img style={{ display: 'none' }} src={ url } alt="" />
  </div>
));

EmbedPlaylistImage.defaultProps = {
  selected: false,
};

const embedPlaylistCaptionStyles = (theme: Theme) => createStyles({
  root: {
    color: theme.palette.grey[50],
    flexGrow: 1,
  }
});

export interface IEmbedPlaylistCaptionProps extends WithStyles<typeof embedPlaylistCaptionStyles> {
  title?: string;
}

export const EmbedPlaylistCaption = withStyles(embedPlaylistCaptionStyles)((
  { classes, title }: IEmbedPlaylistCaptionProps
) => (
  <div className={ classes.root }>
    <Typography variant="body1" color="inherit">{ title }</Typography>
  </div>
));

export default EmbedPlaylist;
