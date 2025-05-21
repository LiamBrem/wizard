# utils.py
from deck import Deck

def resolve_trick_static(trick, lead_suit, trump_suit):
    def card_strength(card):
        if card.rank == 'W':
            return (3, 0)
        elif card.rank == 'E':
            return (0, 0)
        elif trump_suit and card.suit == trump_suit:
            return (2, Deck.ranks.index(card.rank))
        elif card.suit == lead_suit:
            return (1, Deck.ranks.index(card.rank))
        else:
            return (0, 0)
    winner = max(trick, key=lambda x: card_strength(x[1]))
    return winner[0]
