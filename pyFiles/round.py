import random
from player import Player
from deck import Deck


class Round:
    def __init__(self, players, round_number):
        self.players = players
        self.round_number = round_number
        self.deck = Deck()
        self.trump_card = None
        self.trump_suit = None
        self.leader_index = 0  # Rotates each round



    def setup_round(self):
        self.deck.reset()
        # Deal cards
        for player in self.players:
            player.receive_cards(self.deck.deal(self.round_number))

        # Determine trump card (next card from deck or None)
        if len(self.deck) > 0:
            self.trump_card = self.deck.deal(1)[0]
            if self.trump_card.rank not in ('W', 'J'):
                self.trump_suit = self.trump_card.suit
            else:
                self.trump_suit = None
        else:
            self.trump_card = None
            self.trump_suit = None

        #print(f"Trump card: {self.trump_card} → Trump suit: {self.trump_suit}")



    def collect_bids(self):
        #print("\n--- Bidding Phase ---")
        bids = []
        for i, player in enumerate(self.players):
            bid = player.make_bid(self.trump_suit, self.round_number, i, len(self.players), bids)
            bids.append(bid)
            #print(f"{player.name} bids {bid}")



    def play_tricks(self):
        #print("\n--- Playing Tricks ---")
        played_cards = []
        for trick_num in range(self.round_number):
            #print(f"\nTrick {trick_num + 1}:")
            trick = []
            lead_suit = None
            for i in range(len(self.players)):
                player_index = (self.leader_index + i) % len(self.players)
                player = self.players[player_index]
                card = player.play_card(trick, lead_suit, self.trump_suit, played_cards)
                if lead_suit is None and card.rank not in ('W', 'E'):
                    lead_suit = card.suit
                #print(f"{player.name} plays {card}")
                trick.append((player_index, card))
                played_cards.append(card)
            winner_index = self.resolve_trick(trick, lead_suit)
            self.players[winner_index].tricks_won += 1
            #print(f"{self.players[winner_index].name} wins the trick")
            self.leader_index = winner_index  # Winner leads next



    def resolve_trick(self, trick, lead_suit):
        def card_strength(card):
            if card.rank == 'W':
                return (3, 0)  # Highest
            elif card.rank == 'E':
                return (0, 0)  # Lowest
            elif self.trump_suit and card.suit == self.trump_suit:
                return (2, Deck.ranks.index(card.rank))
            elif card.suit == lead_suit:
                return (1, Deck.ranks.index(card.rank))
            else:
                return (0, 0)

        winner = max(trick, key=lambda x: card_strength(x[1]))
        return winner[0]
    


    @staticmethod
    def resolve_trick_static(trick, lead_suit, trump_suit):
        def card_strength(card):
            if card.rank == 'W':
                return (3, 0)  # Highest tier
            elif card.rank == 'E':
                return (0, 0)  # Lowest tier
            elif trump_suit and card.suit == trump_suit:
                return (2, Deck.ranks.index(card.rank))
            elif lead_suit and card.suit == lead_suit:
                return (1, Deck.ranks.index(card.rank))
            else:
                return (0, 0)

        winner = max(trick, key=lambda x: card_strength(x[1]))
        return winner[0]
    


    def calculate_scores(self):
        scores = {}
        for player in self.players:
            if player.tricks_won == player.bid:
                scores[player.name] = 20 * player.bid
            else:
                scores[player.name] = -abs(10 * (player.tricks_won - player.bid))
        return scores



    def show_results(self):
        pass
        #print("\n--- Round Results ---")
        #for player in self.players:
            #print(f"{player.name} - Bid: {player.bid}, Tricks Won: {player.tricks_won}")



    def play_round(self):
        self.setup_round()
        self.collect_bids()
        self.play_tricks()
        self.show_results()
        return self.calculate_scores()
