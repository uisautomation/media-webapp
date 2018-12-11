import * as React from 'react';

import { createStyles, Theme, withStyles, WithStyles } from '@material-ui/core/styles';

import PlaylistOverlay from '../components/PlaylistOverlay';

import PlaylistJWPConfigurationProvider from '../providers/PlaylistJWPConfigurationProvider';

import GenericEmbedPage from './GenericEmbedPage';

const styles = (theme: Theme) => createStyles({
  playerRoot: {
    paddingRight: theme.spacing.unit * 16 + 1,
  },
});

export interface IProps extends WithStyles<typeof styles> {
  match: { params: { pk: string; }; };
}

export const PlaylistEmbedPage = withStyles(styles)((
  { classes, match: { params: { pk } } }: IProps
) => (
  <GenericEmbedPage
    id={pk}
    ConfigurationProvider={PlaylistJWPConfigurationProvider}
    errorTitle="This playlist could not be displayed"
    errorMessage="You may need to sign in to an account with permission to view the content."
    classes={{ playerRoot: classes.playerRoot }}
  >
    <PlaylistOverlay />
  </GenericEmbedPage>
));

export default PlaylistEmbedPage;
