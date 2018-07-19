import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { withMathJax } from '../providers/MathJaxProvider';

/**
 * Render inline or display math from TeX source.
 *
 * This component should be a descendent of `MathJaxProvider` if math rendering is desired.
 */
class TeXMath extends Component {
  constructor(props) {
    super(props);
    this.root = React.createRef();
  }

  componentDidMount() {
    this.synchroniseWithMathJax();
  }

  componentDidUpdate() {
    this.synchroniseWithMathJax();
  }

  synchroniseWithMathJax() {
    const { MathJax } = this.props;
    if(!MathJax || !MathJax.Hub || !this.root.current) { return; }
    MathJax.Hub.Queue(['Typeset', MathJax.Hub, this.root.current]);
  }

  render() {
    const { display, source, MathJax } = this.props;
    const type = 'math/tex' + (display ? '; mode=display' : '');
    if(!MathJax) {
      if(display) {
        return <pre><code>{ source }</code></pre>
      } else {
        return <code>{ source }</code>;
      }
    } else {
      return <script ref={this.root} type={ type }>{ source }</script>;
    }
  }
};

TeXMath.propTypes = {
  /** TeX math-mode source. */
  source: PropTypes.string.isRequired,

  /** Indicate that the source should be typeset in display mode (as opposed to inline). */
  display: PropTypes.bool,
};

TeXMath.defaultProps = {
  display: false,
};

export default withMathJax(TeXMath);
