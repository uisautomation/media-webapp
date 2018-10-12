// Adapted from:
// https://gist.github.com/int128/e0cdec598c5b3db728ff35758abdbafd

// Watch builds are only used in development
process.env.NODE_ENV = 'development';

const fs = require('fs-extra');
const paths = require('react-scripts-ts/config/paths');
const webpack = require('webpack');
const config = require('react-scripts-ts/config/webpack.config.dev.js');

// Allow overriding the output directory via the APP_BUILD environment variable.
if(process.env.APP_BUILD) {
  console.log('Overriding output directory:', process.env.APP_BUILD);
  paths.appBuild = process.env.APP_BUILD;
}

config.output.path = paths.appBuild;
paths.publicUrl = config.output.path + '/';

webpack(config).watch({}, (err, stats) => {
  if (err) {
    console.error(err);
  } else {
    copyPublicFolder();
  }
  console.error(stats.toString({
    chunks: false,
    colors: true
  }));
});

function copyPublicFolder() {
  fs.copySync(paths.appPublic, paths.appBuild, {
    dereference: true,
    filter: file => file !== paths.appHtml
  });
}
