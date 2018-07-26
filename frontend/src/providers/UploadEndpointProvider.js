import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { mediaUploadGet } from '../api';

const { Provider, Consumer } = React.createContext();

/**
 * Provides an upload endpoint URL to a rendered child component via the uploadUrl prop. While the
 * endpoint is being fetched, renders the child component passing null as the uploadUrl prop.
 *
 * Unrecognised props on UploadEndpointProvider are broadcast to the child component.
 */
class UploadEndpointProvider extends Component {
  constructor(props) {
    super(props);
    this.state = { url: null };
  }

  render() {
    return <Provider value={ this.state.url }>{ this.props.children }</Provider>
  }

  componentDidUpdate(prevProps, prevState) {
    if((prevProps.item !== this.props.item) && this.props.item) {
      // The item changed and was truthy => start fetching an upload endpoint
      setTimeout(() => this.fetchUploadEndpoint(), 0);
    }
  }

  fetchUploadEndpoint() {
    const { item } = this.props;
    // Don't do anything if we have no item
    if(!item) { return; }

    // Try to fetch the upload endpoint for the media item. If the URL is null, wait for a bit and
    // try again. This wait is necessary because upload endpoints may not be created at the same
    // time as media items depending on Media Platform backend.
    mediaUploadGet(item).then(({ url }) => {
      if(!url) { setTimeout(() => this.fetchUploadEndpoint(), 500); return; }
      this.setState({ url });
    });
  }
}

UploadEndpointProvider.propTypes = {
  /** Media item resource as returned by the API. */
  item: PropTypes.object,
};

UploadEndpointProvider.defaultProps = {
  item: null,
};

/**
 * A higher-order component wrapper which passes the upload endpoint URL to its vhild via the
 * uploadUrl prop.
 */
const withUploadEndpoint = WrappedComponent => props => (
  <Consumer>{ value => <WrappedComponent uploadUrl={ value } {...props} />}</Consumer>
);

export { UploadEndpointProvider, withUploadEndpoint };
export default UploadEndpointProvider;
