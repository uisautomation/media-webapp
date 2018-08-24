## Examples

An anonymous user has a sign in link:

```js
const profile = { isAnonymous: true };

<NavigationPanel profile={ profile }/>
```

A signed in user has their display name shown along with a sign out link.

```js
const profile = {
    isAnonymous: false,
    username: 'test0001',
    displayName: 'Tesing Software',
};

<NavigationPanel profile={ profile }/>
```

If the ``avatarImageUrl`` property is set, it is used for the avatar:

```js
const profile = {
    isAnonymous: false,
    username: 'test0001',
    displayName: 'Tesing Software',
    avatarImageUrl: 'http://via.placeholder.com/100x60',
};

<NavigationPanel profile={ profile }/>
```
