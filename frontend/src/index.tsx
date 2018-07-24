import * as React from 'react';
import * as ReactDOM from 'react-dom';

import { BrowserRouter, Route } from 'react-router-dom'

import IndexPage from './pages/IndexPage';
import MediaPage from './pages/MediaPage';

ReactDOM.render(
  <BrowserRouter>
    <div>
      <Route exact={true} path="/" component={IndexPage} />
      <Route exact={true} path="/media/:pk" component={MediaPage} />
    </div>
  </BrowserRouter>,
  document.getElementById('app')
);
