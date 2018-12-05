import * as React from 'react';

import Button from '@material-ui/core/Button';
import Divider from '@material-ui/core/Divider';
import Typography from '@material-ui/core/Typography';

import { createStyles, Theme, withStyles, WithStyles } from '@material-ui/core/styles';

const styles = (theme: Theme) => createStyles({
  root: {
    border: `1px solid ${theme.palette.grey[300]}`,
    borderRadius: theme.spacing.unit * 2,
    color: theme.palette.grey[300],
    padding: theme.spacing.unit * 2,
  },

  buttonContainer: {
    display: 'flex',
    flexDirection: 'row-reverse',
    justifyContent: 'flex-end',
  },

  dividerRoot: {
    backgroundColor: theme.palette.grey[300],
    margin: `${theme.spacing.unit * 2}px 0`,
  },
});

export interface IProps extends WithStyles<typeof styles> {
  /** The title of the dialog. */
  title: string;

  /** A human friendly message directing the user to sign in. */
  message: string;

  /** An optional technical description of the error. */
  technicalDescription?: string;

  /** Whether to show a sign-in button. */
  showSignIn?: boolean;
};

/**
 * A dialog suitable for display on the embed page which displays a title, human readable message
 * and, optionally, a technical error message and a sign in button.
 */
export const EmbedMessageDialog = withStyles(styles)((
  { classes, title, message, technicalDescription, showSignIn }: IProps
) => (
  <div className={ classes.root }>
    <Typography color="inherit" variant="title" gutterBottom={ true }>
      { title }
    </Typography>
    <Typography color="inherit" variant="body2" gutterBottom={ true }>
      { message }
    </Typography>

    {
      technicalDescription
      ?
      <Typography color="inherit" variant="caption" gutterBottom={ true }>
        { technicalDescription }
      </Typography>
      :
      null
    }

    {
      showSignIn
      ?
      <>
        <Divider classes={{ root: classes.dividerRoot }} />

        <div className={classes.buttonContainer}>
          <Button variant="contained" color="primary" component="a" href={ getSignInURL() }>
            Sign in
          </Button>
        </div>
      </>
      :
      null
    }
  </div>
));


EmbedMessageDialog.defaultProps = {
  showSignIn: true,
};


// Return a sign-in URL which will redirect back to the current page.
const getSignInURL = () => (
  `/accounts/login?next=${encodeURIComponent(location.pathname)}`
);

export default EmbedMessageDialog;
