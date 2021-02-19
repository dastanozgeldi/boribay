import toml
from discord.ext.ipc import Client
from quart import Quart, render_template

data = toml.load('../config.toml')['ipc']
app = Quart(__name__)
web_ipc = Client(secret_key=data['secret_key'])


@app.route('/')
async def home_page():
	stats = await web_ipc.request('get_general_stats')
	return await render_template('index.html', stats=stats)


if __name__ == '__main__':
	app.run(debug=True)
