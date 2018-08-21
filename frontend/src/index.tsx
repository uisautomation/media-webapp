import * as React from 'react';
import * as ReactDOM from 'react-dom';

import { BrowserRouter, Route } from 'react-router-dom'

import AnalyticsPage from './pages/AnalyticsPage';
import ChannelPage from './pages/ChannelPage';
import IndexPage from './pages/IndexPage';
import MediaEditPage from './pages/MediaEditPage';
import MediaPage from './pages/MediaPage';
import PlaylistCreatePage from './pages/PlaylistCreatePage';
import PlaylistEditPage from './pages/PlaylistEditPage';
import PlaylistPage from './pages/PlaylistPage';
import StaticTextPage from './pages/StaticTextPage';
import UploadPage from './pages/UploadPage';

ReactDOM.render(
  <BrowserRouter>
    <div>
      <Route exact={true} path="/" component={IndexPage} />
      <Route exact={true} path="/media/:pk" component={MediaPage} />
      <Route exact={true} path="/media/:pk/analytics" component={AnalyticsPage} />
      <Route exact={true} path="/media/:pk/edit" component={MediaEditPage} />
      <Route exact={true} path="/upload" component={UploadPage} />
      <Route exact={true} path="/channels/:pk" component={ChannelPage} />
      <Route exact={true} path="/create_playlist" component={PlaylistCreatePage} />
      <Route exact={true} path="/playlists/:pk" component={PlaylistPage} />
      <Route exact={true} path="/playlists/:pk/edit" component={PlaylistEditPage} />
      <Route exact={true} path="/about" component={StaticTextPage} />
    </div>
  </BrowserRouter>,
  document.getElementById('app')
);
