import * as React from 'react';

import JWPlayerProvider from '../providers/JWPlayerProvider';

export interface IState {
  playlist: any[];

  index: number;
}

export interface IChildProps extends IState {
  setIndex: (index: number) => void;
}

export interface IProps {
  children: (props: IChildProps) => React.ReactNode;
}

/**
 * Provide the current JWPlayer player's playlist and playlist index to its children along with a
 * function which can be used to change the current playlist index.
 *
 * The child must be a function which accepts an object with the playlist, index and index setting
 * function.
 *
 * Example:
 *
 * ```jsx
 * <JWPlayerProvider>
 *   <JWPlayerPlaylistProvider>{
 *    ({ playlist, index, setIndex }) => { ... }
 *   }</JWPlayerPlaylistProvider>
 *   ...
 * </JWPlayerProvider>
 * ```
 */
export const JWPlayerPlaylistProvider = (props: IProps) => (
  // We wrap an inner component so that we can convert the function argument into a prop on the
  // inner component.
  <JWPlayerProvider.Consumer>{
    jwplayer => <JWPlayerPlaylistProviderInner jwplayer={ jwplayer } {...props} />
  }</JWPlayerProvider.Consumer>
);

// The inner component takes the same props as JWPlayerPlaylistProvider but with an extra jwplayer
// prop.
interface IInnerProps extends IProps {
  jwplayer: JWPlayer | null;
}

class JWPlayerPlaylistProviderInner extends React.Component<IInnerProps, IState> {
  constructor(props: any) {
    super(props);
    this.state = { playlist: [], index: 0 };
  }

  public componentDidMount() {
    // When the component first mounts, perform any actions required on the JWPlayer API object.
    this.jwplayerChanged();
  }

  public componentDidUpdate(prevProps: IInnerProps) {
    const { jwplayer } = this.props;

    // If it has changed, perform any actions required on the JWPlayer API object.
    if(jwplayer !== prevProps.jwplayer) {
      this.jwplayerChanged();
    }
  }

  public render() {
    const { children } = this.props;
    return children ? children({ setIndex: this.setIndex.bind(this), ...this.state}) : null;
  }

  private setIndex(index: number) {
    const { jwplayer } = this.props;

    // Don't do anything if there is no JWPlayer API object.
    if(jwplayer) { jwplayer.playlistItem(index); }
  }

  private jwplayerChanged() {
    const { jwplayer } = this.props;

    // If the object is null, nothing more need be done.
    if(!jwplayer) { return; }

    // Wire up event handlers and set initial state from API object.
    jwplayer.on('playlist', ({ playlist }) => this.setState({ playlist }));
    jwplayer.on('playlistItem', ({ index }) => this.setState({ index }));
    this.setState({
      index: jwplayer.getPlaylistIndex(),
      playlist: jwplayer.getPlaylist(),
    });
  }
}

export default JWPlayerPlaylistProvider;
