### Examples

```js
source = `## The Quadratic Formula

In **mathematics**, the *quadratic formula* is the solution to
<$>ax^2 + bx + c</$> in terms of <$>x</$>:

\`\`\`math
x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}.
\`\`\`
`;

const { MathJaxProvider } = require('../providers/MathJaxProvider');

<MathJaxProvider>
  <h3>Input</h3>
  <pre><code>{ source }</code></pre>

  <h3>Output</h3>
  <RenderedMarkdown source={ source } />
</MathJaxProvider>
```

