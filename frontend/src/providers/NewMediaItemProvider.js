import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { mediaCreate } from '../api';

const { Provider, Consumer } = React.createContext();

/**
 * Create a new media item resource and provide it to child components via the withNewMediaItem
 * HoC. Before the item is created, the provided item is null.
 */
class NewMediaItemProvider extends Component {
  constructor(props) {
    super(props);
    this.state = { item: null };
  }

  componentWillMount() {
    const { title } = this.props;
    mediaCreate({ title }).then(item => this.setState({ item }));
  }

  render() {
    return <Provider value={ this.state.item }>{ this.props.children }</Provider>
  }
}

NewMediaItemProvider.propTypes = {
  /** Title for the newly created media item. */
  title: PropTypes.string,
};

NewMediaItemProvider.defaultProps = {
  title: 'Untitled',
};

/**
 * A higher-order component wrapper which passes the newly created media item resource to its
 * child. The item is passed in the item prop.
 */
const withNewMediaItem = WrappedComponent => props => (
  <Consumer>{ value => <WrappedComponent item={ value } {...props} />}</Consumer>
);

export { NewMediaItemProvider, withNewMediaItem };
export default NewMediaItemProvider;
