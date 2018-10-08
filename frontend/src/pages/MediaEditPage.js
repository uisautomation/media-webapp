import React, { Component } from 'react';
import { Helmet } from 'react-helmet';

import { Link, Redirect } from 'react-router-dom'

import Grid from '@material-ui/core/Grid';
import Button from '@material-ui/core/Button';
import Typography from '@material-ui/core/Typography';
import { withStyles } from '@material-ui/core/styles';

import Page from '../containers/Page';
import BodySection from '../components/BodySection';
import ItemMetadataForm from "../components/ItemMetadataForm";
import {mediaGet, mediaPatch} from "../api";
import { showMessage } from "../containers/Snackbar";
import IfOwnsChannel from "../containers/IfOwnsChannel";

/**
 * A page which allows the user to edit a media item's metadata.
 */
class MediaEditPage extends Component {
  state = {
    // An error object as returned by the API or the empty object if there are no errors.
    errors: {},

    // The primary key of the item being edited.
    itemId: null,

    // The media item resource being edited by the ItemMetadataForm.
    item: { },

    // The item being edited has been successfully saved.
    saveSuccess: false,
  };

  /** Gets the media item's id. */
  getItemId = () => this.props.match.params.pk;

  /**
   * Retrieve the item.
   */
  componentWillMount() {
    this.fetchIfNecessary();
  }

  componentDidUpdate() {
    this.fetchIfNecessary();
  }

  /**
   * Examine the pk prop and decide if we need to fetch a media item to populate the form.
   */
  fetchIfNecessary() {
    const { match: { params: { pk } } } = this.props;
    const { itemId } = this.state;
    if(pk !== itemId) {
      this.setState({ itemId: pk, saveSuccess: false });
      mediaGet(pk).then(item => (item.id === pk) && this.setState({ item }));
    }
  }

  /**
   * Save the edited item.
   */
  save() {
    const { item } = this.state;

    // Cannot save an item with no id.
    if(!item.id) { return; }

    mediaPatch(item)
      .then(() => {
        showMessage('The media item has been updated.');
        this.setState({ saveSuccess: true });
      })
      .catch(({ body }) => this.setState({ errors: body })
    );
  }

  render() {
    const { classes } = this.props;
    const { item, itemId, errors, saveSuccess } = this.state;

    if(saveSuccess) { return <Redirect to={'/media/' + itemId} />; }

    return (
      <Page gutterTop>
        <Helmet><title>Edit media item</title></Helmet>
        <BodySection>
          <IfOwnsChannel channel={item && item.channel}>
            <Grid container justify='center'>
              <Grid item xs={12} sm={10} md={8} lg={6}>
                <ItemMetadataForm
                  item={item}
                  errors={errors}
                  onChange={patch => this.setState({item: {...item, ...patch}})}
                />
                <div className={ classes.buttonSet }>
                  <Button
                    variant='outlined' component={ Link } to={ '/media/' + this.getItemId() }
                  >
                    Cancel
                  </Button>
                  <Button color='secondary' variant='contained' onClick={ () => this.save() } >
                    Save
                  </Button>
                </div>
              </Grid>
            </Grid>
          </IfOwnsChannel>
          <IfOwnsChannel channel={item && item.channel} hide>
            <Typography variant="headline" component="div">
              You cannot edit this media item.
            </Typography>
          </IfOwnsChannel>
        </BodySection>
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
});

export default withStyles(styles)(MediaEditPage);
