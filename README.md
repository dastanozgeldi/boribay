<h2 align="center">
  <img src="https://cdn.discordapp.com/attachments/766571630268252180/827824066869985280/circle.png" height='100px' width='100px'>
</h2>

<h1 align="center">Boribay 💂‍♂️</h1>
<h4 align="center">A Discord Bot created to make people smile.</h4>

<h1 align="center">
  <a href="https://top.gg/bot/735397931355471893">
    <img src="https://top.gg/api/widget/servers/735397931355471893.svg" />
  </a>

  <a href="https://top.gg/bot/735397931355471893">
    <img src="https://top.gg/api/widget/upvotes/735397931355471893.svg" />
  </a>

  <a href="https://top.gg/bot/735397931355471893">
    <img src="https://top.gg/api/widget/owner/735397931355471893.svg" />
  </a>
</h1>

## Setting up the bot configuration.
- Create `config.json` file inside `./data` directory.
- Paste there the code below.
- Edit for your personal purposes.
```json
{
  "bot": {
    "beta": false,  // Is the bot currently in the maintenance mode.
    "errors_log": 12345678,  // Channel ID where you'd like to log errors.
    "token": "The bot token",
    "exts": [  // A list of cogs to load by default.
        "boribay.extensions.help",
        "boribay.extensions.economy",
        "boribay.extensions.fun",
        "boribay.extensions.images",
        "boribay.extensions.misc",
        "boribay.extensions.moderation",
        "boribay.extensions.settings",
        "boribay.extensions.useful"
    ]
  },
  "database": {  // Database credential, the bot uses PostgreSQL.
    "user": "someone",
    "password": "wowimaguy",
    "host": "localhost",
    "database": "Boribay"  // More likely to name the DB Boribay.
  },
  "links": {
    "webhook": "The webhook URL you'd like to log new servers of the bot in.",
    "invite": "https://discord.com/api/oauth2/authorize?client_id=735397931355471893&permissions=8&scope=bot",
    "github": "https://github.com/Dositan/Boribay/",
    "support": "https://discord.gg/ZAzTFTCerM/",
    "top_gg": "https://top.gg/bot/735397931355471893#/"
  },
  "api": {
    "weather": "API key from https://openweathermap.org/",
    "dagpi": "API key from https://dagpi.xyz/",
    "alex": "API key from https://api.alexflipnote.dev/"
  }
}
```

<h3 align="center"><a href="https://discord.com/api/oauth2/authorize?client_id=735397931355471893&permissions=8&scope=bot">Invite Boribay</a> | <a href="https://discord.gg/ZAzTFTCerM">Support Server</a> | <a href="https://boribay.netlify.app/">Website</a></h3>
