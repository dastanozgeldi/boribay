from game import TicTacToe
import random


class Player:
	def __init__(self, letter):
		# letter is x or o
		self.letter = letter

	def get_move(self, game):
		pass


class RandomComputerPlayer(Player):
	def __init__(self, letter):
		super().__init__(letter)

	def get_move(self, game: TicTacToe):
		square = random.choice(game.available_moves())
		return square


class HumanPlayer(Player):
	def __init__(self, letter):
		super().__init__(letter)

	def get_move(self, game: TicTacToe):
		valid_square = False
		val = None
		while not valid_square:
			square = int(input(self.letter + '\'s turn. Input move (0-8): '))
			try:
				val = square
				if val not in game.available_moves():
					raise ValueError
				valid_square = True
			except ValueError:
				print('Invalid square. Try again.')

		return val
