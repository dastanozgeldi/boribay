**__What changes have been implemented in v1.1.4?__**

**General**:
1. Almost all commands got detailed help for them.

**Useful**:
1. new command "youtube", where you simply search for videos from youtube.

**Moderation**:
1. every single command now belongs to its appropriate category.

2. new commands: "role create", "role delete".

3. error prediction to avoid issues that have been happening with users.

**Economics**:
1. "pay" command was renamed to "transfer" and now you specify member firstly,
then the amount of money to transfer.

2. in mod "balance add", "balance remove" you also should provide the member
firstly, this is made since users were stuck at this a lot.

3. "daily" command has been removed. This is such an useless thing. 2 database
calls a day to just get random amount of Batyrs was not interesting.

4. "work" got some real challenges: number reversing and guessing the length.

5. "coinflip" was moved to the "Fun" extension,
implemented "headsandtails" command instead, where you bet your real choice.

**Coming soon:** The Boribay website, API, Internationalization.