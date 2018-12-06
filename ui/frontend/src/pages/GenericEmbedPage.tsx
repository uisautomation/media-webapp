import * as React from 'react';

import CircularProgress from '@material-ui/core/CircularProgress';

import { createStyles, Theme, withStyles, WithStyles } from '@material-ui/core/styles';

import EmbedMessageDialog from '../components/EmbedMessageDialog';
import ResponsiveJWPlayerPlayer from '../components/ResponsiveJWPlayerPlayer';

import { ChildFunction } from '../providers/GenericJWPConfigurationProvider';
import JWPlayerProvider from '../providers/JWPlayerProvider';

const styles = (theme: Theme) => createStyles({
  root: {
    backgroundColor: 'black',
    display: 'flex',
    height: '100%',
    left: 0,
    position: 'absolute',
    top: 0,
    width: '100%',
  },

  // A child of the root which will center a child element horizontally and vertically. Useful for
  // loading indicators, dialog boxes, etc.
  centered: {
    alignItems: 'center',
    display: 'flex',
    height: '100%',
    justifyContent: 'center',
    width: '100%',
  },

  playerRoot: {
    height: '100%',
    width: '100%',
  },

  dialogRoot: {
    margin: theme.spacing.unit * 2,
    maxWidth: theme.spacing.unit * 45,
  },

  contentRoot: {
    flexGrow: 1,
  },

  messageRoot: {
    margin: theme.spacing.unit * 2,
  },
});

export interface IConfigurationProviderProps {
  id: string;

  children: ChildFunction;
}

export interface IProps extends WithStyles<typeof styles> {
  /** The id passed to ConfigurationProvider */
  id: string;

  /**
   * One of {MediaItem,Playlist}JWPConfigurationProvider. Used to fetch the JWP configuration used
   * to populate the player.
   */
  ConfigurationProvider: React.ComponentType<IConfigurationProviderProps>;

  /**
   * Children are rendered within the JWPlayerProvider context of the player.
   */
  children?: React.ReactNode;

  /**
   * If there is an error, use this title in the error dialog.
   */
  errorTitle: string;

  /**
   * If there is an error, use this human-friendly message.
   */
  errorMessage: string;
}

// Options passed to JWPlayer setup() method in addition to the playlists.
const SETUP_OPTIONS = {
  aspectratio: "16:9",
  width: "100%",
};

/**
 * A generic player embed page which can handle individual media items or playlists. By default a
 * full-screen player is rendered showing the configuration provided by the passed configuration
 * component.
 *
 * Children of this component are rendered within the JWPlayerProvider context of the player and so
 * may add additional UI.
 */
export const GenericEmbedPage = withStyles(styles)((
  { id, ConfigurationProvider, children, classes, errorTitle, errorMessage } : IProps
) => (
  <div className={classes.root}>
    <JWPlayerProvider>
      <ConfigurationProvider id={id}>{
        ({ setupOptions, errorResponse, isFetching }) => {
          // If we're fetching the playlist, show a loading indicator.
          if(isFetching) {
            return <div className={ classes.centered }><CircularProgress /></div>;
          }

          // If there is no playlist in the setup options, something has gone wrong. Display a
          // generic error message with specific information for developers. We also do this if the
          // playlist is empty because JWPlayer can't deal with having nothing at all to display.
          if(!setupOptions || !setupOptions.playlist || setupOptions.playlist.length === 0) {
            // Build technical error description.
            const errorDescription = [];
            if(errorResponse) {
              errorDescription.push(`Error code: ${errorResponse.status}.`);
            }
            if(setupOptions && setupOptions.playlist && setupOptions.playlist.length === 0) {
              errorDescription.push('No media items were present.');
            }

            return <div className={ classes.centered }>
              <EmbedMessageDialog
                classes={{ root: classes.messageRoot }}
                title={ errorTitle }
                message={ errorMessage }
                technicalDescription={ errorDescription.join(' ') }
              />
            </div>;
          }

          // Otherwise, render the children
          return <>
            <ResponsiveJWPlayerPlayer
              initialSetupOptions={{ ...SETUP_OPTIONS, ...setupOptions }}
              classes={{ root: classes.playerRoot }}
            />
            { children }
          </>;
        }
      }</ConfigurationProvider>
    </JWPlayerProvider>
  </div>
));

export default GenericEmbedPage;
