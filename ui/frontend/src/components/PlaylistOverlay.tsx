import * as React from 'react';

import classNames from 'classnames';

import Drawer from '@material-ui/core/Drawer';
import Fade from '@material-ui/core/Fade';
import IconButton from '@material-ui/core/IconButton';
import Input from '@material-ui/core/Input';

import LeftIcon from '@material-ui/icons/KeyboardArrowLeft';

import { createStyles, Theme, withStyles, WithStyles } from '@material-ui/core/styles';

import {
  EmbedPlaylist, EmbedPlaylistCaption, EmbedPlaylistImage, EmbedPlaylistItem
} from '../components/EmbedPlaylist';

import JWPlayerPlaylistProvider from '../providers/JWPlayerPlaylistProvider';

const styles = (theme: Theme) => createStyles({
  root: { },

  playlist: {
    flexGrow: 1,
    maxWidth: '100vw',
    overflowY: 'scroll',
    width: theme.spacing.unit * 48,
  },

  drawerPaper: {
    backgroundColor: 'rgba(0, 0, 0, 0.74)',
    color: theme.palette.grey[50],
    display: 'flex',
    flexDirection: 'column',
    overflowX: 'hidden',
  },

  drawerOpen: {
    maxWidth: '100vw',
    transition: theme.transitions.create('width'),
    width: theme.spacing.unit * 48,
  },

  drawerClose: {
    transition: theme.transitions.create('width'),
    width: theme.spacing.unit * 16 + 1,
  },

  expandIcon: {
    transition: theme.transitions.create('transform'),

    '&:hover': {
      backgroundColor: 'rgba(255, 255, 255, 0.12)',
    }
  },

  expandIconOpen: {
    transform: 'rotate(-180deg)',
  },

  expandIconClose: {
    transform: 'rotate(0deg)',
  },

  topBar: {
    alignItems: 'center',
    display: 'flex',
    marginBottom: theme.spacing.unit,
    marginRight: theme.spacing.unit,
    marginTop: theme.spacing.unit,
  },

  searchInput: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: theme.spacing.unit * 0.5,
    color: 'inherit',
    flexGrow: 1,
    paddingBottom: theme.spacing.unit,
    paddingLeft: theme.spacing.unit * 2,
    paddingRight: theme.spacing.unit * 2,
    paddingTop: theme.spacing.unit,
  },
});

interface IProps extends WithStyles<typeof styles> { }

interface IState {
  drawerOpen: boolean;

  searchText: string;
}

/**
 * An overlay for the embedded playlist page showing the current playlist.
 *
 * The overlay includes the current playlist and a search box. It can be collapsed to the left-hand
 * side via an arrow button.
 */
export const PlaylistOverlay = withStyles(styles)(
  class extends React.Component<IProps, IState> {
    constructor(props: any) {
      super(props);
      this.state = { drawerOpen: true, searchText: '' };
    }

    public render() {
      // The lambdas are used in the playlist rendering. I can't think of a clean way to remove
      // them. - RJW
      //
      // tslint:disable jsx-no-lambda

      const { classes } = this.props;
      const { drawerOpen, searchText } = this.state;

      // Event handlers
      const toggleDrawer = () => this.setState({ drawerOpen: !drawerOpen });
      const setSearchText = (event: React.ChangeEvent<HTMLInputElement>) => (
        this.setState({ searchText: event.target.value })
      );

      // Function which can filter playlist items.
      const filterPlaylistItem = (item: any) => {
        if(searchText === '') { return true; }
        const searchLower = searchText.toLowerCase();
        if((item.title || '').toLowerCase().indexOf(searchLower) !== -1) { return true; }
        if((item.description || '').toLowerCase().indexOf(searchLower) !== -1) { return true; }
        return false;
      };

      return (
        <Drawer
          variant="permanent" anchor="right"
          classes={{
            paper: classNames(classes.drawerPaper, {
              [classes.drawerOpen]: drawerOpen,
              [classes.drawerClose]: !drawerOpen,
            }),
          }}
          open={ drawerOpen }
        >
          <div className={ classes.topBar }>
            <IconButton
              color="inherit" onClick={ toggleDrawer }
              classes={{
                root: classNames(classes.expandIcon, {
                  [classes.expandIconOpen]: drawerOpen,
                  [classes.expandIconClose]: !drawerOpen,
                })
              }}
            >
              <LeftIcon />
            </IconButton>
            <Fade in={ drawerOpen }>
              <Input
                classes={{ root: classes.searchInput }}
                disableUnderline={ true }
                placeholder="Search"
                value={ searchText }
                onChange={ setSearchText }
              />
            </Fade>
          </div>
          <JWPlayerPlaylistProvider>{
            ({ playlist, index, setIndex }) => (
              <EmbedPlaylist classes={{ root: classes.playlist }}>{
                playlist.filter(filterPlaylistItem).map((item, itemIndex) => (
                  <EmbedPlaylistItem
                    onClick={() => setIndex(itemIndex)}
                    selected={ itemIndex === index }
                    key={ itemIndex }
                  >
                    <EmbedPlaylistImage selected={ itemIndex === index } url={ item.image }/>
                    <EmbedPlaylistCaption title={ item.title } />
                  </EmbedPlaylistItem>
                ))
              }</EmbedPlaylist>
            )
          }</JWPlayerPlaylistProvider>
        </Drawer>
      );
    }
  }
);

export default PlaylistOverlay;
