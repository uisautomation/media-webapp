import React from 'react';
import PropTypes from 'prop-types';

import Fade from '@material-ui/core/Fade';
import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import { withStyles } from '@material-ui/core/styles';

import Page from '../containers/Page';
import BodySection from '../components/BodySection';
import RenderedMarkdown from '../components/RenderedMarkdown';

class StaticTextPage extends React.Component {
  state = { source: null };

  componentDidMount() {
    // When the component mounts, fetch the corresponding text for the document. For a page at
    // /foo/bar, this should be /foo/bar.md.
    const { match: { url } } = this.props;
    if(url) {
      // If we know the URL of this page, fetch the corresponding markdown source.
      fetch(url + '.md')
        .then(response => {
          if(response.ok) { return response.text(); }
          throw new Error(`Error getting static text from server: ${response.status}`);
        })
        .then(source => this.setState({ source }));
    }
  }

  render() {
    const { classes } = this.props;
    const { source } = this.state;
    return <Page gutterTop classes={{ gutterTop: classes.pageGutterTop }}>
      <Fade in={Boolean(source)}>
        <Grid container justify='center' className={ classes.container }>
          <Grid item xl={4} lg={6} md={8} sm={10} xs={12}>
            <BodySection
              component={Paper}
              componentProps={{ classes: { root: classes.paperRoot, rounded: classes.paperRounded } }}
            >
              <RenderedMarkdown source={ source || '' } />
            </BodySection>
          </Grid>
        </Grid>
      </Fade>
    </Page>
  }
}

StaticTextPage.propTypes = {
  classes: PropTypes.object.isRequired,
};

const styles = theme => ({
  container: {
    height: '100%',

    [theme.breakpoints.up('sm')]: {
      height: 'auto',
      marginBottom: theme.spacing.unit * 3,
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
      boxShadow: 'none',
    },
  },
});

export default withStyles(styles)(StaticTextPage);
