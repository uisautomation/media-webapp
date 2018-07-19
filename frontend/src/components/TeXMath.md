### Examples

The ``source`` prop specifies the TeX math-mode source which is used for
typesetting. Note that the component needs to be a descendant of
``MathJaxProvider``.

```js
const { MathJaxProvider } = require('../providers/MathJaxProvider');

<MathJaxProvider>
  The double angle formula for <TeXMath source='\\sin(2 \\theta)' /> is as follows:
  <TeXMath display source='\\sin(2 \\theta) = 2 \\sin \\theta \\cos \\theta.' />
</MathJaxProvider>
```

If the component is not a descendant of ``MathJaxProvider``, then the ``code``
tag will be used as a fall-back.

```js
<p>
The double angle formula for <TeXMath source='\\sin(2 \\theta)' /> is as follows:
<TeXMath display source='\\sin(2 \\theta) = 2 \\sin \\theta \\cos \\theta.' />
</p>
```
