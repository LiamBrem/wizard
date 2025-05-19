import random
from deck import Deck, Card
from simulation import simulate_trick_outcome, prob_win


RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', 'W', 'E']


# Other Players
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.bid = 0
        self.tricks_won = 0

    def receive_cards(self, cards):
        self.hand = cards

    def make_bid(self, trump_suit, round_number, position, total_players, bids_so_far=None):
        self.bid = random.randint(0, round_number // 2)
        return self.bid
    
    def legal_cards(self, lead_suit):
        if lead_suit:
            cards = [card for card in self.hand if card.suit == lead_suit and card.rank not in ('W', 'E')]
            return cards if cards else self.hand
        return self.hand

    def play_card(self, trick_so_far, lead_suit, trump_suit, played_cards=None):
        card = random.choice(self.legal_cards(lead_suit))
        self.hand.remove(card)
        return card
    
    def reset(self):
        self.bid = 0
        self.tricks_won = 0


    

class EvolvedPlayer(Player):
    def __init__(self, name, genome):
        super().__init__(name)
        self.genome = genome

    def evaluate_card(self, card, trump_suit):
        g = self.genome.genes

        if card.rank == 'W':  # Wizard
            return g["wizard_weight"]
        elif card.rank == 'E':  # Jester
            return g["jester_weight"]

        # Normal card
        base_strength = (RANKS.index(card.rank) + 2) / 14  # Normalize to [0,1]
        if trump_suit and card.suit == trump_suit:
            return base_strength * g["trump_weight"]
        else:
            return base_strength * g["high_card_weight"]

    def make_bid(self, trump_suit, round_number, position, total_players, bids_so_far=None):
        g = self.genome.genes

        # 1. Evaluate hand strength
        score = sum(self.evaluate_card(c, trump_suit) for c in self.hand)

        # 2. Position bias (later position = higher value)
        if "position_bias" in g:
            normalized_pos = position / (total_players - 1) if total_players > 1 else 0
            score += g["position_bias"] * normalized_pos

        # 3. Risk bias
        score += g["risk_bias"]

        # 4. Over-bidding awareness
        if bids_so_far and "overbid_penalty_weight" in g:
            estimated_bid = round(score)
            total_bids = sum(bids_so_far) + estimated_bid
            excess = max(0, total_bids - round_number)
            score -= g["overbid_penalty_weight"] * excess

        # 5. Finalize bid
        self.bid = max(0, min(round_number, round(score)))
        return self.bid
    
    def update_memory(self, played_cards):
        self.played_cards = played_cards

    def play_card(self, trick_so_far, lead_suit, trump_suit, played_cards):
        legal = self.legal_cards(lead_suit)

        # Play defensively if you've hit your bid
        if self.tricks_won >= self.bid:
            card = min(legal, key=lambda c: self.evaluate_card(c, trump_suit))
        else:
            card = max(legal, key=lambda c: self.evaluate_card(c, trump_suit))

        self.hand.remove(card)
        return card
    


class ProbabilityPlayer(Player):
    def __init__(self, name):
        super().__init__(name)

    def make_bid(self, trump_suit, round_number, position, total_players, bids_so_far=None):
        # Bids based purely on the summed probability of each card winning a trick.
        
        probs = [
            prob_win(card, self.hand, trump_suit, total_players, round_number)
            for card in self.hand
        ]

        expected_tricks = sum(probs)
        self.bid = max(0, min(round_number, round(expected_tricks)))
        return self.bid
    
    def play_card(self, trick_so_far, lead_suit, trump_suit, played_cards):
        legal = self.legal_cards(lead_suit)

        # Use prob_win instead of evaluate_card
        if self.tricks_won >= self.bid:
            # Defend (lose)
            card = min(
                legal,
                key=lambda c: prob_win(c, self.hand, trump_suit, 4, len(self.hand))
            )
        else:
            # Attack (win)
            card = max(
                legal,
                key=lambda c: prob_win(c, self.hand, trump_suit, 4, len(self.hand))
            )

        self.hand.remove(card)
        return card
