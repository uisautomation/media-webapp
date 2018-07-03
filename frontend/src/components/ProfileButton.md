### Examples

```js
const profile = {
    is_anonymous: false,
    username: 'mb2174'
};

<ProfileButton profile={profile} variant="raised" color="secondary" />
```

```js
// Nobody is signed in.

const profile = {
    is_anonymous: true,
    urls: {
        login: 'https://single.sign.on/login'
    }
};

<ProfileButton profile={profile} variant="raised" color="primary" />
```
