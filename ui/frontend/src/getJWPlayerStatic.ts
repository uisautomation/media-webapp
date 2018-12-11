/**
 * Return a Promise which is resolved with the static JWPlayer API object. For example, to register
 * a div with the id "myPlayer":
 *
 * ```js
 * getJWPlayerStatic().then(jwplayer => jwplayer('myPlayer').setup({ ... }));
 * ```
 *
 * The arguments to pass to ``setup()`` are documented in the JWPlayer API reference[1].
 *
 * Behind the scenes, this function will determine if the JWPlayer library has already been loaded
 * and, if not, add a new script tag to the end of the document body doing so. The script tag is
 * only added once and so it is safe to call this function from within any component which needs
 * the JWPlayer library loaded.
 *
 * [1] https://developer.jwplayer.com/jw-player/docs/javascript-api-reference/#jwplayer-div-setup-options
 */
export const getJWPlayerStatic = (() => {
  // A promise which is resolved with the global JWPlayer object. If no script has ever been
  // loaded, this will be null. In order to allow this to be what would be called in C a "static
  // variable", we make use of the immediate function invocation trick where the function which
  // defines this variable is immediately invoked allowing us to use it as a static variable in the
  // returned function.
  let scriptPromise: null | Promise<JWPlayerStatic> = null;

  return (): Promise<JWPlayerStatic> => {
    // If there is already a script-loading promise, return it instead.
    if(scriptPromise) { return scriptPromise; }

    // Create a script tag which will load the library.
    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = '/lib/player.js';

    // Create a promise which resolves itself when the script is loaded.
    scriptPromise = new Promise<JWPlayerStatic>(resolve => {
      script.onload = () => {
        if(!jwplayer) { throw new Error('JWPlayer not loaded'); }
        resolve(jwplayer);
      };
    });

    // Add the script tag to the end of the body.
    const body = document.getElementsByTagName('body')[0];
    if(!body) {
      throw new Error('Document has no <body>!');
    }
    body.appendChild(script);

    return scriptPromise;
  };
})();

export default getJWPlayerStatic;
