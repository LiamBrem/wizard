from deck import Deck
from player import Player, ProbabilityPlayer, HumanPlayer, EvolvedPlayer
from round import Round
from genome import Genome


class WizardGame:
    def __init__(self, player_name, bot_names):
        best_genome_data = {'high_card_weight': 0.5023165514298096, 'wizard_weight': 1.4714515692989907, 'jester_weight': -0.48924459142903415, 'trump_weight': 1.482564655282382, 'position_bias': -0.11277887936317726, 'risk_bias': -0.935420498563112, 'overbid_penalty_weight': 0.55397505598976}
        total_rounds = 60 // (len(bot_names) + 1)
        self.players = [HumanPlayer(player_name)] + [EvolvedPlayer(name, Genome(genes=best_genome_data)) for name in bot_names]
        self.total_rounds = total_rounds
        self.scores = {p.name: 0 for p in self.players}
        self.current_round = 0
        self.current_round_obj = None

    def start_next_round(self):
        self.current_round += 1
        round_size = self.current_round
        self.current_round_obj = Round(self.players, round_size)
        self.current_round_obj.setup_round()
        return self.current_round_obj  # don't collect bids yet

    def collect_bids_after_human(self):
        self.current_round_obj.collect_bids()
        return self.current_round_obj.get_bids()

    def update_scores(self, round_scores):
        for name, score in round_scores.items():
            self.scores[name] += score

    def is_game_over(self):
        return self.current_round >= self.total_rounds
