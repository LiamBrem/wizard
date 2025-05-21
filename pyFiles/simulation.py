from deck import Deck, Card
from utils import resolve_trick_static
import random
import pandas as pd


def simulate_trick_outcome(self_card, player_hand, trump_suit, lead_suit, num_players, simulations=1000):
    
    # simulate many random completions of a trick and return how often self_card wins.
    win_count = 0
    all_cards = [Card(suit, rank) for suit in Deck.suits for rank in Deck.ranks]
    known_cards = player_hand + [self_card]
    
    for _ in range(simulations):
        # Step 1: Build a pool of remaining unknown cards
        remaining_deck = [card for card in all_cards if card not in known_cards]

        # Step 2: Randomly deal to opponents
        simulated_trick = [(0, self_card)]  # You play first
        for pid in range(1, num_players):
            opp_card = random.choice(remaining_deck)
            simulated_trick.append((pid, opp_card))
            remaining_deck.remove(opp_card)

        # Step 3: Resolve trick
        winner_idx = resolve_trick_static(simulated_trick, lead_suit, trump_suit)
        if winner_idx == 0:
            win_count += 1

    return win_count / simulations



def prob_win(card, hand, trump_suit, num_players, round_number, use_cutoff=2):
    lead_suit = card.suit if card.rank not in ('W', 'E') else None
    return simulate_trick_outcome(
        self_card=card,
        player_hand=[c for c in hand if c != card],
        trump_suit=trump_suit,
        lead_suit=lead_suit,
        num_players=num_players
    )


