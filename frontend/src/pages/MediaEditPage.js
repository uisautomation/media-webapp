import React, { Component } from 'react';

import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import { withStyles } from '@material-ui/core/styles';

import Page from '../containers/Page';
import ItemMetadataForm from "../components/ItemMetadataForm";
import {mediaGet, mediaPatch} from "../api";

/**
 * A page which allows the user to edit a media item's metadata.
 */
class MediaEditPage extends Component {
  constructor({ match: { params: { pk } } }) {
    super();

    // remember the media item's key for convenience
    this.pk = pk;

    this.state = {
      // An error object as returned by the API or the empty object if there are no errors.
      errors: {},
      // The media item being edited by the ItemMetadataForm.
      item: {},
    };
  }

  /**
   * Retrieve the item.
   */
  componentWillMount() {
    mediaGet(this.pk).then(item => this.setState({ item }));
  }

  /**
   * Save the edited item.
   */
  save() {
    mediaPatch(this.state.item)
      .then(savedItem => { location = '/media/' + this.pk })
      .catch(({ body }) => this.setState({ errors: body }));
  }

  render() {
    const { classes } = this.props;
    const { item, errors } = this.state;
    return (
      <Page>
        <section className={classes.section}>
          <Grid container justify='center'>
            <Grid item xs={12} sm={10} md={8} lg={6}>
              <ItemMetadataForm
                item={item}
                errors={errors}
                onChange={patch => this.setState({item: {...item, ...patch}})}
              />
              <div className={ classes.buttonSet }>
                <Button variant='outlined' href={ '/media/' + this.pk } >
                  Cancel
                </Button>
                <Button color='primary' variant='outlined' onClick={ () => this.save() } >
                  Save
                </Button>
              </div>
            </Grid>
          </Grid>
        </section>
      </Page>
    );
  }
}

const styles = theme => ({
  buttonSet: {
    '& button': {
      marginLeft: theme.spacing.unit,
    },
    marginTop: theme.spacing.unit,
    textAlign: 'right',
  },
  section: {
    marginTop: theme.spacing.unit,
  },
});

export default withStyles(styles)(MediaEditPage);
