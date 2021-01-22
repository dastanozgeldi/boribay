import toml

from discord.ext.ipc import Client
from quart import Quart, render_template

data = toml.load('../config.toml')['ipc']
app = Quart(__name__)
web_ipc = Client(host=data['host'], secret_key=data['secret_key'])


@app.route('/')
async def welcoming_page():
	return 'Welcome!'


@app.route('/home')
async def home_page():
	return await render_template('home.html', title='Home')


@app.route('/about')
async def about_page():
	return await render_template('about.html', title='About')


@app.route('/stats')
async def stats_page():
	return await app.node.request('get_stats_page')


@app.route('/commands')
async def commands_page():
	return await app.node.request('get_commands_page')


@app.before_first_request
async def before():
	app.node = await web_ipc.discover()


if __name__ == '__main__':
	app.run(debug=True)
