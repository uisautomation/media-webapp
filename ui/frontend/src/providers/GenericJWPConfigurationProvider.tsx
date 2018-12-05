// The code below is used to turn a media item response from the UI API endpoint into something
// which can be passed to jwplayer(...).setup(). It's a little non-obvious how it does this so this
// comment explains the general idea.
//
// The UI API endpoint returns a response of the following form:
//
//  {
//    "mediaItems": [
//      {
//        "id": "string",
//        "title": "string",
//        "description": "string",
//        "playlistUrl": "url"
//      },
//      ...
//    ]
//  }
//
// The playlistUrl field in each item points to a JWPlayer delivery API playlist URL which encodes
// the content of the media item. The response from that URL consists of a body with the following
// form:
//
//  {
//    // some other stuff
//
//    "playlist": [
//      {
//        "file": "Actual URL for JWPlayer player",
//        // some other stuff
//      },
//      // ... etc for other videos
//    ]
//  }
//
// JWP intends the "playlist" value to be passed into the jwplayer(...).setup() function and we
// will do so but we want to a) combine these values together from each media item and b) add in
// the fields provided by the UI API endpoint. We want to merge in values because the Google
// Analytics integration with JWPlayer will only label events based on values in the playlist and
// we want to use the media id as a label.
//
// So, we need to fetch all the playlists and then merge them together.
//
// The fetchAndParseAsJson() function below is responsible for fetching the playlist. So, the media
// item example from above becomes:
//
//  {
//    "title": "string",
//    "description": "string",
//    "playlistUrl": "url",
//    "playlist": {
//      // JSON parsed response from playlistUrl...
//      "playlist": [
//        // JWPlayer-specific items
//      ],
//    }
//  }
//
// The code in GenericJWPConfigurationProvider.fetchResource() takes each media item returned from
// the UI API endpoint and passes it through fetchAndParseAsJson(). Each item is then folded into
// the playlist returned from fetchAndParseAsJson(). So, if the fetched media items look like this:
//
//  {
//    "mediaItems": [
//      {
//        "id": "xyz",
//        "title": "my title",
//        "description": "my description",
//        "playlistUrl": "https://example.invalid/pl1",
//        "playlist": {
//          "playlist": [
//            {
//              "file:" "https://jwp.invalid/file1.mp4"
//            },
//            {
//              "file:" "https://jwp.invalid/file2.mp4"
//            }
//          ],
//        }
//      },
//      {
//        "id": "abc",
//        "title": "another title",
//        "description": "another description",
//        "playlistUrl": "https://example.invalid/pl2",
//        "playlist": {
//          "playlist": [
//            {
//              "file:" "https://jwp.invalid/file3.mp4"
//            },
//            {
//              "file:" "https://jwp.invalid/file4.mp4"
//            }
//          ],
//        }
//      }
//    ]
//  }
//
// They end up as a playlist which looks like this:
//
//  [
//    {
//      "id": "xyz",
//      "title": "my title",
//      "description": "my description",
//      "playlistUrl": "https://example.invalid/pl1",
//      "file:" "https://jwp.invalid/file1.mp4"
//    },
//    {
//      "id": "xyz",
//      "title": "my title",
//      "description": "my description",
//      "playlistUrl": "https://example.invalid/pl1",
//      "file:" "https://jwp.invalid/file2.mp4"
//    },
//    {
//      "id": "abc",
//      "title": "another title",
//      "description": "another description",
//      "playlistUrl": "https://example.invalid/pl2",
//      "file:" "https://jwp.invalid/file3.mp4"
//    },
//    {
//      "id": "abc",
//      "title": "another title",
//      "description": "another description",
//      "playlistUrl": "https://example.invalid/pl2",
//      "file:" "https://jwp.invalid/file4.mp4"
//    }
//  ]
//
// This playlist can now be passed directly to jwplayer(...).setup().

import * as React from 'react';

import {
  IJWPConfigurationResponse,
  IMediaItemJWPConfiguration
} from '../uiapi';

export type JWPConfigurationFetchFunction = (id: string) => Promise<IJWPConfigurationResponse>;

export interface IChildArguments {
  setupOptions?: { [x: string]: any };
  errorResponse?: Response;
  isFetching: boolean;
}

export type ChildFunction = (props: IChildArguments) => React.ReactNode;

export interface IProps {
  id: string;

  fetchFunction: JWPConfigurationFetchFunction;

  children: ChildFunction;
}

// The state is just the arguments we pass to the child.
type IState = IChildArguments;

/**
 * Generic component to fetch a JWP player configuration from the UI and massage it into something
 * which can be passed to the JWPlayer API jwplayer(...).setup() method.
 *
 * Example:
 *
 * import { playlistJWPConfigurationGet } from 'uiapi'
 *
 * <GenericJWPConfigurationProvider id="abcd1234" fetchFunction={ playlistJWPConfigurationGet }>
 *  {({ setupOptions, error, isFetching }) => ( ... )}
 * }</GenericJWPConfigurationProvider>
 */
export class GenericJWPConfigurationProvider extends React.Component<IProps, IState> {
  constructor(props: any) {
    super(props);
    this.state = { isFetching: false };
  }

  public componentDidMount() {
    this.fetchResource();
  }

  public componentDidUpdate(prevProps: IProps) {
    const { id } = this.props;
    if(id !== prevProps.id) {
      this.fetchResource();
    }
  }

  public render() {
    const { children } = this.props;
    return children(this.state);
  }

  private fetchResource() {
    const { id, fetchFunction } = this.props;
    if(!id) { return; }

    // Reset state before fetching.
    this.setState({ isFetching: true, errorResponse: undefined, setupOptions: undefined });

    // Perform the fetch, updating the state from the response.
    fetchFunction(id).then(({body, response}) => {
      if(!response.ok || !body) {
        this.setState({ errorResponse: response, isFetching: false });
        return;
      }

      const { mediaItems } = body;
      return Promise.all(mediaItems.map(fetchAndParseAsJson)).then(items => {
        // This any[] type matches the one specified in
        // https://github.com/DefinitelyTyped/DefinitelyTyped/blob/master/types/jwplayer/index.d.ts
        let combinedPlaylist: any[] = [];

        // See the comment at the top of this file which explains what this pipeline does.
        items.map(item => {
          combinedPlaylist = combinedPlaylist.concat(item.playlist.playlist.map(
            jwplayerPlaylist => ({ ...item, ...jwplayerPlaylist })
          ))
        });

        // Write the combined playlist to the new state.
        this.setState({ setupOptions: { playlist: combinedPlaylist }, isFetching: false });
      });
    });
  }
}

interface IFetchResult extends IMediaItemJWPConfiguration {
  playlist: {
    playlist: any[];

    [x: string]: any;
  };
}

const fetchAndParseAsJson = (item: IMediaItemJWPConfiguration): Promise<IFetchResult> => (
  fetch(item.playlistUrl).then(response => {
    if(!response.ok) {
      // tslint:disable-next-line
      console.error(`Error fetching ${item.playlistUrl}:`, response);
      throw Error('Fetch failed');
    }

    return response.json().then(playlist => ({ ...item, playlist }));
  })
);

export default GenericJWPConfigurationProvider;
