// A component which provides plumbing to register a new JWPlayer player div and to allow other
// components to access the accompanying jwplayer API object. See the component documentation for
// an overview of how this works.
import * as React from 'react';

import getJWPlayerStatic from '../getJWPlayerStatic';

// These are the props taken by the Player component provided by JWPlayerProvider.
export interface IJWPlayerPlayerProps {
  /**
   * An object providing the initial options passed to jwplayer(...).setup() when this player is
   * registered. Changing these props will not re-register the player after it is configured.
   */
  initialSetupOptions?: { [x: string]: any };
}

// We make use of two contexts in this provider. One context provides a player component down to be
// rendered by one of the children. The other context provides a configured JWPlayer API object
// which points at that player. The reason we use two contexts is that we don't want a consumer of
// the player component context to needlessly re-render itself after the player is registered and
// the associated JWPlayer API object is created which would happen if we has a single context
// passing both values.
const PlayerContext = React.createContext<React.SFC<IJWPlayerPlayerProps>>(() => null);
const JWPlayerContext = React.createContext<JWPlayer | null>(null);

export interface IProps {
  children: React.ReactNode;
}

export interface IState {
  jwplayer: JWPlayer | null;
}

/**
 * The JWPlayerProvider component provides JWPlayer API integration. The general idea is that all
 * components which are a child of this one all are interested in the same player. For example,
 * children of this component can contain components positioning and styling the player itself and
 * also components showing the current playlist for the player.
 *
 * The player itself will be rendered by the JWPlayerProvider.Player component. For example to
 * allow for positioning/styling a player within the provider, you can nest the player within a
 * <div>:
 *
 * ```jsx
 * <JWPlayerProvider>
 *  <div className="..."><PlayerTitle /></div>
 *  <div className="..."><JWPlayerProvider.Player /></div>
 * </JWPlayerProvider>
 * ```
 *
 * Here, the fictional ``PlayerTitle`` component is a connected component which subscribes to the
 * configures JWPlayer API object for the player and displays the current title.
 *
 * A component can be passed the current JWPlayer API object by means of the
 * ``JWPlayerProvider.Consumer`` component. This component takes a single child which is a function
 * which is passed the JWPlayer API object for the player. Components can then subscribe to
 * JWPlayer events on the object. For example, a component which displays the current volume could
 * be written as follows:
 *
 * ```jsx
 * class PlayerVolume extends React.Component {
 *    constructor(props) {
 *      super(props);
 *      this.state = { jwplayer: null, volume: null };
 *    }
 *
 *    render() {
 *      const { jwplayer, volume } = this.state;
 *      return <JWPlayerProvider.Consumer>{
 *        updatedjwplayer => {
 *          if(updatedjwplayer !== jwplayer) {
 *            // We have a new player, subscribe to volume change events.
 *            updatedjwplayer.on('volume', ({ volume }) => this.setState({ volume }));
 *
 *            // Store the player object and current volume in the state.
 *            this.setState({ jwplayer: updatedjwplayer, volume: updatedjwplayer.getVolume() });
 *          }
 *          return (volume === null) ? null : <div>volume: { volume }</div>
 *        }
 *      }</JWPlayerProvider.Consumer>;
 *    }
 * }
 * ```
 */
export class JWPlayerProvider extends React.Component<IProps, IState> {
  /**
   * A component which passes the configured JWPlayer API object to its child or null if there is no
   * such object. The child must be a function which takes a single value as a function. For example:
   *
   * ```jsx
   * <JWPlayerProvider>
   *   ...
   *   <JWPlayerProvider.Consumer>
   *    { jwplayer => <div>Playlist length: { jwplayer.getPlaylist().length }</div> }
   *   </JWPlayerProvider.Consumer>
   *   ...
   * </JWPlayerProvider>
   * ```
   *
   * The component *must* be a child of a JWPlayerProvider and will be passed the JWPlayer API object
   * corresponding to the player within the provider.
   */
  public static Consumer = JWPlayerContext.Consumer;

  /**
   * A convenience component which renders the Player component from the current JWPlayerProvider
   * context. All props are passed to the Player component. For example:
   *
   * ```jsx
   * <JWPlayerProvider>
   *   ...
   *   <JWPlayerProvider.Player initialSetupOptions={{ width: 640, height: 480 }} />
   *   ...
   * </JWPlayerProvider>
   * ```
   */
  public static Player: React.SFC<IJWPlayerPlayerProps> = props => (
    <PlayerContext.Consumer>{ Player => <Player {...props}/> }</PlayerContext.Consumer>
  );

  // A component which renders the JWPlayer player itself. This component will register itself with
  // the JWPlayer API and cause the value returned by JWPlayerContext to be updated with the
  // configured jwplayer object. The setup() method is called before the JWPlayerContext value is
  // updated.
  private PlayerComponent: React.SFC<IJWPlayerPlayerProps>;

  // When the component is mounted, this is set to the return value of getJWPlayerStatic(). This is
  // done to make sure we kick off the asynchronous load of the JWPlayer library ASAP rather than
  // waiting for the actual player div to be mounted.
  private staticPromise: Promise<JWPlayerStatic>;

  constructor(props: any) {
    super(props);

    this.state = { jwplayer: null };

    // Create the player component itself. The component is specific to the class because it uses a
    // ref callback bound to the registerPlayerDiv() method. When the Player component is mounted,
    // the ref callback is called by React and is passed the actual HTML element for the player.
    // The registerPlayerDiv() method then takes that element and uses the JWPlayer API to render
    // the player into it.
    const refCallback = this.registerPlayerDiv.bind(this);
    this.PlayerComponent = ({ initialSetupOptions }) => (
      <div ref={ (element: HTMLDivElement) => refCallback(element, initialSetupOptions) } />
    );
  }

  public componentDidMount() {
    // As an optimisation, kick off the fetching of the JWPlayer library as soon as the component
    // is mounted rather than waiting for the player component to be mounted.
    this.staticPromise = getJWPlayerStatic();
  }

  public render() {
    const { children } = this.props;
    const { jwplayer } = this.state;
    const { PlayerComponent } = this;
    return (
      <PlayerContext.Provider value={ PlayerComponent }>
        <JWPlayerContext.Provider value={ jwplayer }>
          { children }
        </JWPlayerContext.Provider>
      </PlayerContext.Provider>
    );
  }

  // Register a player div and return a promise which is fulfilled with the jwplayer object ready
  // to have setup() called on it.
  private registerPlayerDiv(
    element: null | HTMLDivElement, initialSetupOptions: { [x: string]: any }
  ) {
    // If the null element is passed, de-register the player.
    if(!element) {
      this.setState({ jwplayer: null });
      return;
    }

    // If the element passed does not have an id, create a random one for it.
    if(element.id === '') {
      element.id = `JWPlayerProvider-player-${Math.random()}`;
    }

    // Setup player and set it as a state variable. We use the staticPromise we stashed away
    // earlier or fall back to calling getJWPlayerStatic() if that promise was not set yet.
    return (this.staticPromise || getJWPlayerStatic()).then(jwplayerStatic => {
      const jwplayer = jwplayerStatic(element.id);
      jwplayer.setup(initialSetupOptions);
      this.setState({ jwplayer });
    });
  }
}

export default JWPlayerProvider;
