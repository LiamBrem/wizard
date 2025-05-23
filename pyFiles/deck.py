
import random

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
    
    def __repr__(self):
        return f"{self.rank}{self.suit}"

class Deck:
    suits = ['♥', '♦', '♣', '♠']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', 'W', 'E']
    
    def __init__(self):
        self.cards = []
        self.reset()
    
    def reset(self):
        self.cards = []
        for suit in self.suits:
            for rank in self.ranks:
                if rank not in ('W', 'E'):  # Regular cards
                    self.cards.append(Card(suit, rank))
                elif rank == 'W':  # Wizards (no suit)
                    self.cards.append(Card(None, 'W'))
                elif rank == 'E':  # Jesters (no suit)
                    self.cards.append(Card(None, 'E'))
        random.shuffle(self.cards)
    
    def deal(self, count):
        if count > len(self.cards):
            raise ValueError(f"Not enough cards to deal {count}")
        dealt = self.cards[:count]
        self.cards = self.cards[count:]
        return dealt
    
    def __len__(self):
        return len(self.cards)
