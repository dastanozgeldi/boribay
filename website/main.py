import os

from discord.ext.ipc import Client
from dotenv import load_dotenv
from quart import Quart, render_template

load_dotenv()
app = Quart(__name__)
web_ipc = Client(host=os.getenv('host'), secret_key=os.getenv('secret_key'))


@app.route('/about')
async def about_page():
	return await render_template('about.html', title='About')


@app.route('/stats')
async def stats_page():
	stats = await app.ipc_node.request('get_stats_page')
	return stats


@app.before_first_request
async def before():
	app.ipc_node = await web_ipc.discover()


if __name__ == '__main__':
	app.run(debug=True)
