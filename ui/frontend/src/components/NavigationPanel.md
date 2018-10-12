## Examples

An anonymous user has a sign in link:

```js
const { BrowserRouter } = require('react-router-dom');

const profile = { isAnonymous: true };

<BrowserRouter>
  <NavigationPanel profile={ profile }/>
</BrowserRouter>
```

A signed in user has their display name shown along with a sign out link.

```js
const { BrowserRouter } = require('react-router-dom');

const profile = {
    isAnonymous: false,
    username: 'test0001',
    displayName: 'Tesing Software',
};

<BrowserRouter>
  <NavigationPanel profile={ profile }/>
</BrowserRouter>
```

If the ``avatarImageUrl`` property is set, it is used for the avatar:

```js
const { BrowserRouter } = require('react-router-dom');

const profile = {
    isAnonymous: false,
    username: 'test0001',
    displayName: 'Tesing Software',
    avatarImageUrl: 'http://via.placeholder.com/100x60',
};

<BrowserRouter>
  <NavigationPanel profile={ profile }/>
</BrowserRouter>
```
