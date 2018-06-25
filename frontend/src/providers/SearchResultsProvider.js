import React, { Component } from 'react';
import PropTypes from 'prop-types';

import {
  mediaList, collectionList, mediaResourceToItem, collectionResourceToItem
} from '../api';

const { Provider, Consumer } = React.createContext();

/**
 * Provide combined media and collection search results to descendent components. The query prop is
 * an object which provides the query which is passed to the API. For the moment this query object
 * has one key: search, a text field which is matched against title and description.
 */
class SearchResultsProvider extends Component {
  constructor() {
    super();
    this.state = {
      error: null,

      isLoading: false,

      // A monotonic index which is used to determine if a response from the API server corresponds
      // to the most recent request.
      lastFetchIndex: 0,

      resultItems: null,
    };
  }

  componentWillMount() {
    // Handle the initial query.
    this.fetchResults();
  }

  componentDidUpdate(prevProps) {
    // If the query changed, fetch new results
    if(this.props.query !== prevProps.query) { this.fetchResults(); }
  }

  fetchResults() {
    const { query } = this.props;
    const { lastFetchIndex } = this.state;
    const fetchIndex = lastFetchIndex + 1;

    this.setState({ isLoading: true, lastFetchIndex: fetchIndex });

    // If there is no query, simply blank all results and return.
    if(query === null) {
      this.setState({ mediaResults: null, collectionResults: null, isLoading: false});
      return;
    }

    const { search } = query;

    const urlParams = new URLSearchParams();
    if(query.search) { urlParams.append('search', query.search) }
    const urlParamsString = urlParams.toString();

    const queryPart = (urlParamsString !== '') ? ('?' + urlParamsString) : '';

    // Otherwise launch the query.
    Promise.all([mediaList(query), collectionList(query)]).then(
      ([mediaBody, collectionsBody]) => {
        // Ignore responses if they aren't in response to the most recent request.
        if(this.state.lastFetchIndex !== fetchIndex) { return; }
        const resultItems = this.mergeResults(mediaBody, collectionsBody)
        this.setState({ resultItems, error: null, isLoading: false });
      },
      error => {
        // Ignore errors if they aren't in response to the most recent request.
        if(this.state.lastFetchIndex !== fetchIndex) { return; }
        this.setState({ results: null, error, isLoading: false });
      }
    );
  }

  mergeResults(mediaResults, collectionResults) {
    // tslint:disable-next-line:no-console
    const { maxCollectionResults } = this.props;
    return [
      ...collectionResults.results.slice(0, maxCollectionResults).map(collectionResourceToItem),
      ...mediaResults.results.map(mediaResourceToItem),
    ];
  }

  render() {
    const { resultItems, isLoading } = this.state;
    const { query, children } = this.props;
    return (
      <Provider value={{query, resultItems, isLoading}}>
        { children }
      </Provider>
    );
  }
}

SearchResultsProvider.propTypes = {
  /** Maximum number of collection results to return. */
  maxCollectionResults: PropTypes.number,

  /** Search query. */
  query: PropTypes.shape({
    search: PropTypes.string,
  }),
};

SearchResultsProvider.defaultProps = {
  maxCollectionResults: 4,
};

/**
 * A higher-order component wrapper which passes the current search results to its child. The
 * following props are provided: resultItems, isLoading and query.
 */
const withSearchResults = WrappedComponent => props => (
  <Consumer>{ results => <WrappedComponent {...results} {...props} /> }</Consumer>
);

export { SearchResultsProvider, withSearchResults };
export default SearchResultsProvider;
