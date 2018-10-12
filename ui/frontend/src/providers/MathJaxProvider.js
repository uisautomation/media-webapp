import React, { Component } from 'react';

const { Provider, Consumer } = React.createContext();

// MathJax CDN link
//
// Non-obviously, the "latest.js" link will always load the latest
// version of MathJax irrespective of the version number in the URL.
// (http://docs.mathjax.org/en/latest/configuration.html#loading-mathjax-from-a-cdn).
//
// We make use of the "safe" variant of MathJax
// (http://docs.mathjax.org/en/latest/safe-mode.html) to limit the ability of
// uploaders to craft MathJax which could expose users to
// contributor-controlled JavaScript.
// (http://docs.mathjax.org/en/latest/safe-mode.html)
//
// TODO: when we have end-to-end browser testing in place, actually *testing*
// that arbitrary JavaScript cannot be inserted is worthwhile.
const MATHJAX_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/latest.js?config=TeX-MML-AM_CHTML,Safe';

/**
 * A provider which will inject the MathJax script into the page and provide the global MathJax
 * object to its children.
 */
class MathJaxProvider extends Component {
  constructor(props) {
    super(props);

    // This is a bit of an anti-pattern but stops us calling setState on an unmounted component if
    // the provider is unmounted before MathJax finishes loading.
    // See https://reactjs.org/blog/2015/12/16/ismounted-antipattern.html
    this._isMounted = false;

    this.state = { MathJax: null };
  }

  componentDidMount() {
    this._isMounted = true;

    // Get the global MathJax object and set it in the state
    getMathJaxPromise().then(MathJax => { if(this._isMounted) { this.setState({ MathJax }); } });
  }

  componentWillUnmount() {
    this._isMounted = false;
  }

  render() {
    const { MathJax } = this.state;
    const { children } = this.props;

    return (
      <Provider value={ MathJax }>
        { children }
      </Provider>
    );
  }
}

/**
 * A higher-order component wrapper which passes the current MathJax global to its child. The
 * profile is passed in the "MathJax" prop.
 */
const withMathJax = WrappedComponent => props => (
  <Consumer>{ value => <WrappedComponent MathJax={value} {...props} />}</Consumer>
);

// Launch or return the MathJax engine promise singleton. The promise is resolved with the
// global MathJax object.
const getMathJaxPromise = () => {
  // If the promise has been created, simply return it.
  if(getMathJaxPromise.__mathJaxPromise) { return getMathJaxPromise.__mathJaxPromise; }

  // Create the promise
  getMathJaxPromise.__mathJaxPromise = new Promise(resolve => {
    window.MathJax = {
      // Function called by MathJax when loaded (but before the queue is set up). Taken from
      // http://docs.mathjax.org/en/latest/configuration.html#using-plain-javascript.
      AuthorInit: () => {
        window.MathJax.Hub.Register.StartupHook("Begin", () => resolve(window.MathJax));
      },
      jax: ["input/TeX","output/CommonHTML"],
      tex2jax: {
        // Since we explicitly create MathJax elements, we disable as much of the "magic" MathJax
        // processing as possible.
        displayMath: [],
        ignoreClass: '.*',
        inlineMath: [],
        processEnvironments: false,
        processEscapes: false,
        processRefs: false,
      }
    };

    // This code is based on the code for dynamically loading MathJax in the documentation.
    // (http://docs.mathjax.org/en/latest/advanced/dynamic.html).
    const head = document.getElementsByTagName("head")[0];
    const script = document.createElement("script");
    script.async = true;
    script.type = 'text/javascript';
    script.src = MATHJAX_CDN;
    head.appendChild(script);
  });

  // Recurse to return promise from globalState.
  return getMathJaxPromise();
};

export { MathJaxProvider, withMathJax };
export default MathJaxProvider;
