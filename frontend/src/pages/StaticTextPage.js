import React from 'react';
import PropTypes from 'prop-types';

import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import { withStyles } from '@material-ui/core/styles';

import Page from '../containers/Page';
import BodySection from '../components/BodySection';
import RenderedMarkdown from '../components/RenderedMarkdown';

class StaticTextPage extends React.Component {
  state = { source: null };

  componentDidMount() {
    // When the component mounts, scan the document for a script tag containing the markdown source
    // for the page.
    const bodyElement = document.getElementById('bodySource');
    if(bodyElement) { this.setState({ source: bodyElement.text }); }
  }

  render() {
    const { classes } = this.props;
    const { source } = this.state;
    return <Page gutterTop classes={{ gutterTop: classes.pageGutterTop }}>
      <Grid container justify='center' className={ classes.container }>
        <Grid item xl={4} lg={6} md={8} sm={10} xs={12}>
          <BodySection component={Paper} classes={{ root: classes.paperRoot, rounded: classes.paperRounded }}>
            <RenderedMarkdown source={ source || '' } />
          </BodySection>
        </Grid>
      </Grid>
    </Page>
  }
}

StaticTextPage.propTypes = {
  classes: PropTypes.object.isRequired,
};

const styles = theme => ({
  container: {
    [theme.breakpoints.down('xs')]: {
      height: '100%',
    },
  },

  pageGutterTop: {
    [theme.breakpoints.down('xs')]: {
      paddingTop: 0,
    },
  },

  paperRoot: {
    minHeight: '100%',
    paddingBottom: theme.spacing.unit * 2,
    paddingTop: theme.spacing.unit * 2,

    [theme.breakpoints.up('sm')]: {
      '& p': {
        textAlign: 'justify',
      },
    },

    '& a': {
      '&:hover': {
        textDecoration: 'underline',
      },
      color: theme.palette.primary.main,
      textDecoration: 'none',
    },
  },

  paperRounded: {
    [theme.breakpoints.down('xs')]: {
      borderRadius: 0,
    },
  },
});

export default withStyles(styles)(StaticTextPage);
