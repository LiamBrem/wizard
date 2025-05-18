import random

class Card:
    suitsSymbols = ["♥️", "♦️", "♣️", "♠️"]

    def __init__(self, suit, rank):
        self.suit = suit  # e.g., 'Hearts'
        self.rank = rank  # e.g., 'Queen'

    def __str__(self):
        if self.suit == "Hearts":
            return f"{self.rank}{self.suitsSymbols[0]}"
        elif self.suit == "Diamonds":
            return f"{self.rank}{self.suitsSymbols[1]}"
        elif self.suit == "Clubs":
            return f"{self.rank}{self.suitsSymbols[2]}"
        elif self.suit == "Spades":
            return f"{self.rank}{self.suitsSymbols[3]}"
        else:
            raise ValueError("Invalid suit")

    def __repr__(self):
        return self.__str__()


class Deck:
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10',
             'J', 'Q', 'K', 'A', 'W', 'E'] # Added wizard and Jester
    
    def __init__(self):
        self.cards = [Card(suit, rank) for suit in self.suits for rank in self.ranks]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards=1): # Deal Num Cards from top of deck
        
        if num_cards > len(self.cards):
            raise ValueError("Not enough cards left to deal.")
        dealt_cards = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt_cards

    def reset(self): # Restore to size & shuffle
        self.__init__()
        self.shuffle()

    def __len__(self):
        return len(self.cards)

    def __str__(self):
        return f"Deck with {len(self.cards)} cards remaining."

    def __repr__(self):
        return self.__str__()
