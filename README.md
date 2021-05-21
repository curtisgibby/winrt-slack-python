# Windows media / Slack Integration

## Why does this exist?

I wanted to be able to push my now-listening status (including album art) to my company's Slack.

## Sounds cool. What do I need to do?

### 1. Create your `config.json` file

```bash
cp config.default.json config.json
```

### 2. Update your `config.json` file

#### Update `slack-token` _(required)_

Open the Slack customization page, e.g. `subdomain.slack.com/customize`. Open the console (F12) and paste:

```javascript
window.prompt("Your API token is: ", TS.boot_data.api_token)
```

Copy the API token from the popup and replace `YOUR_SLACK_TOKEN` with your actual token.

#### Update `emoji-name` _(optional)_

Replace `my-album-art` with your desired Slack emoji name

#### Update `time-format` _(optional)_

Replace `%X` with your desired [datetime formatting string](https://strftime.org/)

### 3. Start your media player

You need to be playing your media _before_ moving on to step 4.

### 4. Run the Python script

```bash
python winrt-track-change-to-slack.py
```

The script will attempt to:

- save your album art as a Slack emoji and
- set your status to the now-playing text including the artist and title and the album-art emoji

```plaintext
[ ] 17:16:14 - Attempting to set status: Now Playing: INXS - Devil Inside
```

If the script is unable to create the album-art emoji (because of a bad token, no local album art, whatever), it will try to set the status using a standard emoji instead, randomly picking one of the following:

- :cd: (`:cd:`)
- :headphones: (`:headphones:`)
- :musical_note: (`:musical_note:`)
- :notes: (`:notes:`)
- :radio: (`:radio:`)

## Whom should I thank?

- Thanks to Jack Ellenberger (@jackellenberger) for his [":slack_on_fire:" article](https://medium.com/@jack.a.ellenberger/slack-on-fire-part-two-please-stop-rotating-my-user-token-replay-attacking-slack-for-emoji-fun-c87da4e54b03) and his emojme library (particularly [`emoji-add.js`](https://github.com/jackellenberger/emojme/blob/e076b58bbe310da154013b51f77d3e1047938983/lib/emoji-add.js#L79-L82)) for helping me figure out how to push an emoji to Slack's [undocumented `/api/emoji.add` endpoint](https://webapps.stackexchange.com/a/126154/35105).
- Thanks to StackOverflow user tameTNT for their [excellent answer](https://stackoverflow.com/questions/65011660/how-can-i-get-the-title-of-the-currently-playing-media-in-windows-10-with-python/66037406#66037406) on how to use Python's `winrt` to get the now-playing song's metadata.
