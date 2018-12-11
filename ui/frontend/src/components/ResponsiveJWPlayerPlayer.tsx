import * as React from 'react';

import { createStyles, Theme, withStyles, WithStyles } from '@material-ui/core/styles';

import JWPlayerProvider, { IJWPlayerPlayerProps } from '../providers/JWPlayerProvider';

const styles = (theme: Theme) => createStyles({
  root: {
    alignItems: 'center',
    display: 'flex',
    justifyContent: 'center',
  },

  // Our trick here is to use the fact that padding values are relative to the container block[1]
  // *width*. We can force a particular aspect ratio by specifying a height of zero and a padding
  // based on the reciprocal of the aspect ratio. We also want the video to have a maximum height
  // of 100vh.  Since the padding value is a function of the containing block width, we need to
  // limit the maximum *width* of that element, not the height. Fortunately we're doing all this
  // jiggery-pokery to keep a constant aspect ratio and so a maximum *height* of 100vh implies a
  // maximum width of 100vh * 16 / 9.
  //
  // [1] https://developer.mozilla.org/en-US/docs/Web/CSS/Containing_block
  container: {
    maxWidth: 'calc(100vh * 16 / 9)',
    position: 'relative',
    width: '100%',
  },

  wrapper: {
    height: 0,
    paddingTop: '56.25%',
    position: 'relative',
    width: '100%',
  },

  player: {
    height: '100%',
    left: 0,
    position: 'absolute',
    top: 0,
    width: '100%',
  },
});

export interface IProps extends WithStyles<typeof styles>, IJWPlayerPlayerProps { };

/**
 * A responsive JWPlayer player. This component must be a child of a JWPlayerProvider component.
 *
 * The component takes exactly the same props as the JWPlayerProvider.Player component.
 *
 * This component wraps the appropriate CSS magic to ensure that the player stays as a centred 16:9
 * player within the page no matter its size. No sizing of the root is provided and so,
 * by default, it will be 0x0. Make sure to add appropriate styling to the root by providing a
 * class name for the root style. E.g:
 *
 * ```jsx
 * const MyComponent = withStyles(...)(({ classes })) => (
 *  <ResponsiveJWPlayerPlayer classes={{ root: classes.someClassName }} />
 * ));
 * ```
 */
export const ResponsiveJWPlayerPlayer = withStyles(styles)((
  { classes, ...playerProps }: IProps
) => (
  // Yes, we really do need all these nested divs to do something as simple as "constant aspect
  // ratio" in CSS. *sigh*
  <div className={ classes.root }>
    <div className={ classes.container }>
      <div className={ classes.wrapper }>
        <div className={ classes.player }>
          <JWPlayerProvider.Player {...playerProps}/>
        </div>
      </div>
    </div>
  </div>
));

export default ResponsiveJWPlayerPlayer;
