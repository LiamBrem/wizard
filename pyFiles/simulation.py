from deck import Deck, Card
from round import Round
import random
import pandas as pd
from player import ProbabilityPlayer, Player


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
        winner_idx = Round.resolve_trick_static(simulated_trick, lead_suit, trump_suit)
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
                score = 20 if p.tricks_won == p.bid else -abs(p.tricks_won - p.bid)
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
