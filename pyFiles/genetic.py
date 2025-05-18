import random
import pandas as pd
from round import Round
from genome import Genome
from player import EvolvedPlayer, Player

POP_SIZE = 30
NUM_GENERATIONS = 75
ELITE_COUNT = 10
GAMES_PER_GEN = 200


def evaluate_generation(population, games_per_bot=GAMES_PER_GEN):
    scores = {p.name: 0 for p in population}
    appearances = {p.name: 0 for p in population}
    game_log = []

    # Flatten the player list enough times to ensure all bots participate equally
    full_pool = []
    while min(appearances.values()) < games_per_bot:
        random.shuffle(population)
        for i in range(0, len(population) - 2):
            group_size = random.randint(3, 6)
            group = population[i:i + group_size - 2]  # 2–4 evolved
            group += [Player(f"Baseline{j}") for j in range(2)]  # 2 fixed bots

            if len(group) < 3:
                continue

            round_number = random.randint(1, 60 // len(group))
            game = Round([p.name for p in group], round_number)
            game.players = group
            scores_dict = game.play_round()

            for p in group:
                if not p.name.startswith("Baseline"):
                    scores[p.name] += scores_dict[p.name]
                    appearances[p.name] += 1
                    p.tricks_won = 0
                    p.bid = 0

            game_log.append([p.name for p in group])

            # Stop early if all players hit their quota
            if all(v >= games_per_bot for v in appearances.values()):
                break

    return scores


def evolve():
    population = [EvolvedPlayer(f"Bot{i}", Genome()) for i in range(POP_SIZE)]

    best_overall = None
    best_score = float("-inf")
    best_genome_data = None

    # Track progress across generations
    history = []

    for gen in range(NUM_GENERATIONS):
        scores = evaluate_generation(population)
        population.sort(key=lambda p: scores[p.name], reverse=True)
        elites = population[:ELITE_COUNT]

        top_bot = elites[0]
        top_score = scores[top_bot.name]

        #print(f"Gen {gen:>3} | Best Score: {top_score:>6.2f}")

        # best overall
        if top_score > best_score:
            best_score = top_score
            best_overall = top_bot
            best_genome_data = top_bot.genome.genes.copy()

        # history
        history.append({
            "generation": gen,
            "best_score": top_score,
            "avg_score": sum(scores.values()) / len(scores),
            "best_bot": top_bot.name
        })

        # new generation
        new_population = elites[:]
        while len(new_population) < POP_SIZE:
            p1, p2 = random.sample(elites, 2)
            child_genome = p1.genome.crossover(p2.genome)
            child_genome.mutate()
            new_population.append(EvolvedPlayer(f"Bot{len(new_population)}", child_genome))

        population = new_population

    df_history = pd.DataFrame(history)
    return df_history, best_genome_data



def validate_best_genome(genome, games=10000, num_players=5):
    evolved_bot = EvolvedPlayer("EvolvedBot", Genome(genes=genome))
    baseline_names = [f"Bot{i}" for i in range(num_players - 1)]
    baseline_bots = [Player(name) for name in baseline_names]

    score_total = 0
    hit_bid_count = 0
    bid_distribution = []

    for _ in range(games):
        players = [evolved_bot] + random.sample(baseline_bots, k=num_players - 1)
        round_number = random.randint(1, 60 // num_players)
        game = Round([p.name for p in players], round_number)
        game.players = players
        game.play_round()

        for p in players:
            if p.name == "EvolvedBot":
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



if __name__ == "__main__":
    pass
    #df_history, best_genome = evolve()
    #validate_best_genome(best_genome, games=1000, num_players=5)

