import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { mediaGet } from '../api';

const { Provider, Consumer } = React.createContext();

/**
 * Get a media item resource and provide it to child components via the withMediaItem
 * HoC. Before the item is fetched, the provided item is null.
 */
class MediaItemProvider extends Component {
  constructor(props) {
    super(props);
    this.state = { item: null };
  }

  componentWillMount() {
    const { id } = this.props;
    mediaGet(id).then(item => this.setState({ item }));
  }

  render() {
    return <Provider value={ this.state.item }>{ this.props.children }</Provider>
  }
}

MediaItemProvider.propTypes = {
  /** Id of media item to retrieve. */
  id: PropTypes.string.isRequired,
};

/**
 * A higher-order component wrapper which passes the newly created media item resource to its
 * child. The item is passed in the item prop.
 */
const withMediaItem = WrappedComponent => props => (
  <Consumer>{ value => <WrappedComponent item={ value } {...props} />}</Consumer>
);

export { MediaItemProvider, withMediaItem };
export default MediaItemProvider;
