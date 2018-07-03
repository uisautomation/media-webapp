import * as React from 'react';
import * as ReactDOM from 'react-dom';

import IndexPage from './pages/IndexPage';
import MediaPage from './pages/MediaPage';

const mappings = {
  'media': <MediaPage/>,
  'root': <IndexPage/>,
};

for (const id in mappings) {
  if (mappings.hasOwnProperty(id)) {
    const element = document.getElementById(id);
    if (element) {
      ReactDOM.render(mappings[id], element as HTMLElement);
    }
  }
}
