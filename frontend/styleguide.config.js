/**
 * Configuration for styleguidist.
 *
 * See: https://react-styleguidist.js.org/docs/configuration.html
 */

module.exports = {
  // For the moment we aren't using any typescript features for components. Once we do so,
  // uncomment the following to allow styleguidist to parse them.
  //
  // propsParser: require('react-docgen-typescript').parse,

  showCode: true,
  showUsage: true,
  webpackConfig: require('react-scripts-ts/config/webpack.config.dev.js'),
};
