import * as React from 'react';

import { IError, IResourceListResponse } from '../api';

export interface IState<Resource> {
  error?: IError;
  isLoading: boolean;
  resources: Resource[];
};

export interface IPassedProps<Query, Resource> extends IState<Resource> {
  query: Query;

  /* And all the props from componentProps. */
  [x: string]: any;
};

export interface IProps<Query, Resource> {
  /** Query to pass to API. */
  query: Query;

  /** Component to pass results to. Defaults to MediaList. */
  component: React.ComponentType<IPassedProps<Query, Resource>>;

  /** Extra props to pass to the rendered component. */
  componentProps?: {[x: string]: any};

  /** API function which fetches resources. */
  fetchResources(query: Query): Promise<IResourceListResponse<Resource>>;
};

/**
 * A component which fetches a list of list of resources and passes them to a contained component.
 */
export class FetchResources<Query, Resource>
  extends React.Component<IProps<Query, Resource>, IState<Resource>>
{
  public static defaultProps = {
    query: {},
  }

  public state: IState<Resource> = {
    isLoading: false,
    resources: [],
  }

  public componentDidMount() {
    this.fetch();
  }

  public componentDidUpdate(prevProps: IProps<Query, Resource>) {
    if(prevProps.query !== this.props.query) {
      this.fetch();
    }
  }

  public render() {
    const { isLoading, resources, error } = this.state;
    const { query, component: Component, componentProps } = this.props;
    const passedProps = { isLoading, resources, error, query };
    return <Component {...componentProps} {...passedProps} />
  }

  private fetch() {
    const { query, fetchResources } = this.props;

    this.setState({ isLoading: true });
    fetchResources(query)
      .then(response => {
        if(this.props.query === query) {
          this.setState({ isLoading: false, resources: response.results, error: undefined });
        }
      })
      .catch(error => {
        if(this.props.query === query) {
          this.setState({ isLoading: false, resources: [], error });
        }
      });
  }
};

export default FetchResources;
