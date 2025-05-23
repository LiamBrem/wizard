
class Genome:
    def __init__(self, genes=None):
        self.genes = genes or {
            "wizard_weight": 0.95,
            "jester_weight": 0.05,
            "trump_weight": 1.5,
            "high_card_weight": 1.0,
            "risk_bias": 0.0,
            "position_bias": 0.1,
            "overbid_penalty_weight": 0.2
        }
