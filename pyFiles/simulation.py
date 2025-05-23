
import random
from pyFiles.deck import Deck, Card

def simulate_trick_outcome(card, hand, trump_suit, num_players, round_length):
    # Simple simulation to estimate probability of winning
    wins = 0
    trials = 100
    
    for _ in range(trials):
        # Create a new deck without the cards we know about
        deck = Deck()
        deck.reset()
        
        # Remove known cards from deck
        for c in hand + [card]:
            for dc in deck.cards[:]:
                if dc.rank == c.rank and dc.suit == c.suit:
                    deck.cards.remove(dc)
                    break
        
        # Simulate other players' cards
        other_cards = []
        for _ in range(num_players - 1):
            if deck.cards:
                other_cards.append(random.choice(deck.cards))
        
        # Determine if our card would win
        if card.rank == 'W':  # Wizard always wins
            wins += 1
        elif card.rank == 'E':  # Jester always loses
            wins += 0
        else:
            # Check if any other card beats ours
            our_strength = (Deck.ranks.index(card.rank), card.suit == trump_suit)
            beaten = False
            
            for other in other_cards:
                if other.rank == 'W':  # Wizard beats everything
                    beaten = True
                    break
                elif other.rank == 'E':  # Jester loses to everything
                    continue
                else:
                    other_strength = (Deck.ranks.index(other.rank), other.suit == trump_suit)
                    if other.suit == card.suit:  # Same suit
                        if other_strength[0] > our_strength[0]:  # Higher rank
                            beaten = True
                            break
                    elif other.suit == trump_suit:  # Trump beats non-trump
                        beaten = True
                        break
            
            if not beaten:
                wins += 1
    
    return wins / trials

def prob_win(card, hand, trump_suit, num_players, round_length):
    # Simplified probability calculation
    if card.rank == 'W':  # Wizard
        return 0.95  # Almost certain win
    elif card.rank == 'E':  # Jester
        return 0.05  # Almost certain loss
    
    # For normal cards
    if trump_suit and card.suit == trump_suit:
        # Trump cards
        rank_value = Deck.ranks.index(card.rank) / len(Deck.ranks)
        return 0.5 + (rank_value * 0.4)  # 0.5 to 0.9 based on rank
    else:
        # Non-trump cards
        rank_value = Deck.ranks.index(card.rank) / len(Deck.ranks)
        return 0.2 + (rank_value * 0.3)  # 0.2 to 0.5 based on rank
