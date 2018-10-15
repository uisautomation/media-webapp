import React, { Component } from 'react';
import { profileGet } from '../api';

const { Provider, Consumer } = React.createContext();

/**
 * Provide profile information for the current user to descendent components. The user profile is
 * the object returned by the /api/profile endpoint.
 */
class ProfileProvider extends Component {
  constructor() {
    super();
    this.state = { profile: null };
  }

  componentWillMount() {
    profileGet().then(profile => this.setState({ profile }));
  }

  render() {
    const { profile } = this.state;
    const { children } = this.props;

    return (
      <Provider value={profile}>
        { children }
      </Provider>
    );
  }
}

/**
 * A higher-order component wrapper which passes the current user profile to its child. The
 * profile is passed in the profile prop.
 */
const withProfile = WrappedComponent => props => (
  <Consumer>{ value => <WrappedComponent profile={value} {...props} />}</Consumer>
);

export { ProfileProvider, withProfile };
export default ProfileProvider;
