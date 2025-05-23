import random
from pyFiles.simulation import simulate_trick_outcome, prob_win
import pandas as pd
import random
from pyFiles.round import Round
from pyFiles.genome import Genome


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


        if not legal:
            raise ValueError(f"No legal cards for player {self.name}. Hand: {self.hand}, Lead suit: {lead_suit}")


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
    

class HumanPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self._pending_bid = None
        self._pending_card = None

    def set_bid(self, bid_value):
        """Set bid from the Streamlit interface."""
        self._pending_bid = bid_value

    def set_card(self, card):
        """Set card from the Streamlit interface (must be a Card object)."""
        self._pending_card = card

    def make_bid(self, trump_suit, round_number, position, total_players, bids_so_far=None):
        if self._pending_bid is None:
            raise ValueError("Bid not set for human player")
        self.bid = self._pending_bid
        self._pending_bid = None  # reset
        return self.bid

    def play_card(self, trick_so_far, lead_suit, trump_suit, played_cards=None):
        legal = self.legal_cards(lead_suit)
        if self._pending_card is None:
            raise ValueError("Card not set for human player")
        if self._pending_card not in legal:
            raise ValueError(f"Invalid card: {self._pending_card}. Legal: {legal}")
        card = self._pending_card
        self._pending_card = None
        self.hand.remove(card)
        return card


def validate_probability_player(games=100, num_players=5):
    prob_bot = ProbabilityPlayer("ProbabilityBot")
    baseline_names = [f"Bot{i}" for i in range(num_players - 1)]
    baseline_bots = [Player(name) for name in baseline_names]

    score_total = 0
    hit_bid_count = 0
    bid_distribution = []

    for _ in range(games):
        players = [prob_bot] + random.sample(baseline_bots, k=num_players - 1)
        round_number = random.randint(1, 60 // num_players)
        game = Round([p.name for p in players], round_number)
        game.players = players
        game.play_round()

        for p in players:
            if p.name == "ProbabilityBot":
                bid_distribution.append(p.bid)
                score = 20 + 10 * p.tricks_won if p.tricks_won == p.bid else -abs(p.tricks_won - p.bid)
                score_total += score
                if p.tricks_won == p.bid:
                    hit_bid_count += 1
                p.tricks_won = 0
                p.bid = 0
            else:
                p.tricks_won = 0
                p.bid = 0

    avg_score = score_total / games
    hit_rate = hit_bid_count / games

    bid_counts = pd.Series(bid_distribution).value_counts().sort_index()
    bid_percentages = (bid_counts / len(bid_distribution) * 100).round(2)

    bid_freq = pd.DataFrame({
        "Count": bid_counts,
        "Percent": bid_percentages.astype(str) + "%"
    })

    df = pd.DataFrame({
        "Metric": ["Avg Score", "Hit Bid %", "Games"],
        "Value": [f"{avg_score:.2f}", f"{hit_rate:.2%}", f"{games}"]
    })

    return df, bid_freq



def compare_players(evolved_genome, games=1000, num_players=5):
    evo_bot = EvolvedPlayer("Evolved", Genome(genes=evolved_genome))
    prob_bot = ProbabilityPlayer("Prob")
    
    bots = [evo_bot, prob_bot]
    results = {bot.name: {"score": 0, "hit_bid": 0, "bids": []} for bot in bots}
    
    #baseline_names = [f"Bot{i}" for i in range(num_players - 2)]
    #baseline_bots = [Player(name) for name in baseline_names]

    baseline_bots = [Player(f"Baseline{i}") for i in range(20)]

    for _ in range(games):
        for bot in bots:
            players = [bot] + random.sample(baseline_bots, k=num_players - 1)
            round_number = random.randint(1, 60 // num_players)
            game = Round([p.name for p in players], round_number)
            game.players = players
            game.play_round()

            for p in players:
                if p.name == bot.name:
                    score = 20 * p.bid if p.tricks_won == p.bid else -abs(10 * (p.tricks_won - p.bid))
                    results[p.name]["score"] += score
                    results[p.name]["hit_bid"] += int(p.tricks_won == p.bid)
                    results[p.name]["bids"].append(p.bid)
                p.tricks_won = 0
                p.bid = 0

    df_summary = pd.DataFrame([
        {
            "Bot": name,
            "Avg Score": res["score"] / games,
            "Hit Bid %": res["hit_bid"] / games * 100,
        }
        for name, res in results.items()
    ])

    df_bids = pd.DataFrame({
        name: pd.Series(res["bids"])
        for name, res in results.items()
    })

    return df_summary, df_bids
