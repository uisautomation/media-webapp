import * as React from 'react';

import { IError } from '../api';

export interface IState<Resource> {
  error?: IError;
  isLoading: boolean;
  resource?: Resource;
};

export interface IPassedProps<Resource> extends IState<Resource> {
  /* And all the props from componentProps. */
  [x: string]: any;
}

export interface IProps<Resource> {
  /** Id of resource to fetch */
  id: string;

  /** Component to pass results to. */
  component: React.ComponentType<IPassedProps<Resource>>;

  /** Extra props to pass to the rendered component. */
  componentProps?: {[x: string]: any};

  /** API function which fetches resource given an id. */
  fetchResource(id: string): Promise<Resource>;
};

/**
 * A component which fetches a single resource and passes it to a contained component.
 */
class FetchResource<Resource> extends React.Component<IProps<Resource>, IState<Resource>> {
  public state: IState<Resource> = {
    isLoading: false,
  }

  public componentDidMount() {
    this.fetch();
  }

  public componentDidUpdate(oldProps: IProps<Resource>) {
    // If the type or id of the resource changed, re-fetch it.
    if(
      (oldProps.fetchResource !== this.props.fetchResource) ||
      (oldProps.id !== this.props.id)
    ) {
      this.fetch();
    }
  }

  public render() {
    const { isLoading, resource, error } = this.state;
    const { component: Component, componentProps } = this.props;
    const passedProps = { isLoading, resource, error };
    return <Component {...componentProps} {...passedProps} />
  }

  private fetch() {
    const { fetchResource, id } = this.props;

    // Clear any previous resource/loading state.
    this.setState({ isLoading: true, resource: undefined });

    // Fetch the resource.
    fetchResource(id)
      .then(resource => {
        if(this.props.id === id) {
          this.setState({ isLoading: false, resource, error: undefined });
        }
      })
      .catch(error => {
        if(this.props.id === id) {
          this.setState({ isLoading: false, resource: undefined, error });
        }
      });
  }
};

export default FetchResource;

