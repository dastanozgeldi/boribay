from quart import Blueprint, render_template, current_app
main = Blueprint('main', __name__)


@main.route('/')
@main.route('/home')
async def home():
	stats = await current_app.request('get_general_stats')
	return await render_template('home.html', title='Home', stats=stats)


@main.route('/commands')
async def commands_page():
	commands = await current_app.request('get_command_list')
	return await render_template('commands.html', title='Commands', commands=commands)


@main.route('/privacy')
async def privacy():
	return await render_template('privacy.html', title='Privacy')
