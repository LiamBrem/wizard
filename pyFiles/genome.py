import random

class Genome:
    def __init__(self, genes=None):
        if genes is None:
            self.genes = {
                "high_card_weight": random.uniform(1.0, 3.0),
                "wizard_weight": random.uniform(0.5, 2.0),
                "jester_weight": random.uniform(-2.0, 0.0),
                "trump_weight": random.uniform(1.0, 3.5),
                "position_bias": random.uniform(-1.0, 0.5),
                "risk_bias": random.uniform(-1.0, 1.0),
                "overbid_penalty_weight": random.uniform(0.5, 2.5),
            }
        else:
            self.genes = genes

    def crossover(self, other):
        return Genome({
            key: random.choice([self.genes[key], other.genes[key]])
            for key in self.genes
        })

    def mutate(self, rate=0.2):
        for key in self.genes:
            if random.random() < rate:
                self.genes[key] += random.uniform(-0.3, 0.3)

                # Clamp to sensible ranges
                if "weight" in key:
                    self.genes[key] = max(-2.0, min(5.0, self.genes[key]))
                elif key == "position_bias":
                    self.genes[key] = max(-2.0, min(1.0, self.genes[key]))
                elif key == "risk_bias":
                    self.genes[key] = max(-1.5, min(1.5, self.genes[key]))
