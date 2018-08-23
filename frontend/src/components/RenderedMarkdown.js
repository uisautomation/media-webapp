import React from 'react';
import PropTypes from 'prop-types';

import remark from 'remark';
import reactRenderer from 'remark-react';
import deepmerge from 'deepmerge';
import sanitizeGhSchema from 'hast-util-sanitize/lib/github.json';
import defaultCodeHandler from 'mdast-util-to-hast/lib/handlers/code';

import Typography from '@material-ui/core/Typography';
import TeXMath from './TeXMath';
import MathJaxProvider from '../providers/MathJaxProvider';

/**
 * A wrapper for `Typography` which renders its source prop as markdown.
 *
 * Unknown props are broadcast to the underlying `Typography` component. The default "component"
 * prop for the `Typography` component is "div".
 *
 * This component should be a descendent of `MathJaxProvider` if math rendering is desired. The
 * markdown dialect supported is "GitHub flavoured markdown" with a custom extension for
 * mathematics rendering. Inline math can be represented by surrounding TeX markp with ``<$>`` and
 * ``</$>`` tags. Display math can be represented by a code block with the language being "math".
 */
const RenderedMarkdown = ({ source, component, ...otherProps }) => (
  <MathJaxProvider>
    <Typography component={ component } {...otherProps}>{ renderMarkdown(source) }</Typography>
  </MathJaxProvider>
);

RenderedMarkdown.propTypes = {
  component: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  source: PropTypes.string.isRequired,
};

RenderedMarkdown.defaultProps = {
  component: 'div'
};

export default RenderedMarkdown;

/* A function which renders markdown into a React component. */
const renderMarkdown = source => remark()
  // Render inline text of the form "<$>...</$>" as a custom MD-AST tag with type "math"
  .use(customTag, { type: 'math', beginMarker: '<$>', endMarker: '</$>' })
  .use(reactRenderer, {
    // Map HAST "math" element into TeXMath components.
    remarkReactComponents: {
      h1: props => <Typography variant='headline' {...props} />,
      h2: props => <Typography variant='title' {...props} />,
      h3: props => <Typography variant='subheading' {...props} />,
      math: TeXMath,
      p: props => <Typography variant='body1' {...props} />,
    },
    // Use the GitHub HTML sanitisation schema extended to support math elements.
    sanitize: deepmerge(sanitizeGhSchema, {
      attributes: { math: [ 'display', 'source' ] },
      tagNames: [ 'math' ],
    }),
    // Custom options to the MD-AST to HAST conversion
    toHast: {
      handlers: {
        // When a code node is encountered whose language is "math", render it as a display math
        // node rather than the <code> element.
        code: (h, node) => {
          const { lang } = node;
          if(node.lang === 'math') {
            return {
              properties: { display: true, source: node.value },
              tagName: 'math',
              type: 'element'
            };
          }
          return defaultCodeHandler(h, node);
        },
        // When a math MD-AST node is encountered, transform it into a "math" element.
        math: (h, node) => {
          return {
            properties: { source: node.value },
            tagName: 'math',
            type: 'element',
          };
        },
      },
    },
  })
  .processSync(source)
  .contents
;

/* A remark plugin which tokenises inline text between a begin and end marker into a custom MDAST
 * node.
 *
 * Based on
 * https://github.com/zestedesavoir/zmarkdown/blob/master/packages/remark-comments/src/index.js */
function customTag({ beginMarker, endMarker, type }) {
  const { Parser, Compiler } = this;

  const locator = (value, fromIndex) => value.indexOf(beginMarker, fromIndex);

  const inlineTokenizer = (eat, value, silent) => {
    const mBegin = value.indexOf(beginMarker);
    const mEnd = value.indexOf(endMarker);
    if(mBegin !== 0 || mEnd === -1) { return; }

    /* istanbul ignore if - never used (yet) */
    if (silent) { return true; }

    const textValue = value.substring(beginMarker.length, mEnd);
    return eat(beginMarker + textValue + endMarker)({
      type, value: textValue
    });
  };
  inlineTokenizer.locator = locator;

  const inlineTokenizers = Parser.prototype.inlineTokenizers;
  const inlineMethods = Parser.prototype.inlineMethods;
  inlineTokenizers[type] = inlineTokenizer;
  inlineMethods.splice(inlineMethods.indexOf('text'), 0, type);

  if(Compiler) {
    const visitors = Compiler.prototype.visitors;
    if (!visitors) { return; }
    visitors[type] = (node) => {
      return beginMarker + node.value + endMarker;
    };
  }
};
