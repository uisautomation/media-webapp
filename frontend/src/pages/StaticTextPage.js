import React from 'react';
import PropTypes from 'prop-types';

import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import { withStyles } from '@material-ui/core/styles';

import Page from '../containers/Page';
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
    return <Page>
      <Grid container justify='center' className={ classes.container }>
        <Grid item component={Paper} xl={4} lg={6} md={8} sm={10} xs={12} className={ classes.paper }>
          <RenderedMarkdown source={ source || '' } />
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
    marginTop: theme.spacing.unit * 2,
  },

  paper: {
    padding: [[theme.spacing.unit * 2, theme.spacing.unit * 3]],
    textAlign: 'justify',

    '& a': {
      '&:hover': {
        textDecoration: 'underline',
      },
      color: theme.palette.primary.main,
      textDecoration: 'none',
    },
  },
});

export default withStyles(styles)(StaticTextPage);
