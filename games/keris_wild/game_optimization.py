"""Optimizer fences for the three locked Keris Wild bet modes."""

from optimization_program.optimization_config import (
    ConstructConditions,
    ConstructParameters,
    ConstructScaling,
    verify_optimization_input,
)


BASE_FEATURE_PROBABILITY = 0.004561629629629629
ANTE_FEATURE_PROBABILITY = 0.011396740740740741
BASE_HIT_PROBABILITY = 0.3130788
ANTE_HIT_PROBABILITY = 0.3146704
BONUS_FREEGAME_PROBABILITY = 0.962450


def _parameters() -> dict:
    return ConstructParameters(
        num_show=5000,
        num_per_fence=10000,
        min_m2m=4,
        max_m2m=10,
        pmb_rtp=1.0,
        sim_trials=5000,
        test_spins=[50, 100, 200],
        test_weights=[0.3, 0.4, 0.3],
        score_type="rtp",
    ).return_dict()


class OptimizationSetup:
    """Target exclusive criteria while preserving each mode's total RTP."""

    def __init__(self, game_config):
        self.game_config = game_config
        self.game_config.opt_params = {
            "base": {
                "conditions": {
                    "wincap": ConstructConditions(
                        rtp=0.000647,
                        av_win=10000,
                        search_conditions=10000,
                    ).return_dict(),
                    "0": ConstructConditions(rtp=0.0, av_win=0, search_conditions=0).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=0.334688,
                        hr=1 / BASE_FEATURE_PROBABILITY,
                        search_conditions={"symbol": "scatter"},
                    ).return_dict(),
                    "basegame": ConstructConditions(
                        rtp=0.631565,
                        hr=1 / (BASE_HIT_PROBABILITY - BASE_FEATURE_PROBABILITY),
                    ).return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": _parameters(),
            },
            "ante": {
                "conditions": {
                    "wincap": ConstructConditions(
                        rtp=0.001078,
                        av_win=10000,
                        search_conditions=10000,
                    ).return_dict(),
                    "0": ConstructConditions(rtp=0.0, av_win=0, search_conditions=0).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=0.552110,
                        hr=1 / ANTE_FEATURE_PROBABILITY,
                        search_conditions={"symbol": "scatter"},
                    ).return_dict(),
                    "basegame": ConstructConditions(
                        rtp=0.409312,
                        hr=1 / (ANTE_HIT_PROBABILITY - ANTE_FEATURE_PROBABILITY),
                    ).return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": _parameters(),
            },
            "bonus_buy": {
                "conditions": {
                    "wincap": ConstructConditions(
                        rtp=0.001970,
                        av_win=10000,
                        search_conditions=10000,
                    ).return_dict(),
                    "0": ConstructConditions(rtp=0.0, av_win=0, search_conditions=0).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=0.964930,
                        hr=1 / BONUS_FREEGAME_PROBABILITY,
                    ).return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": _parameters(),
            },
        }
        verify_optimization_input(self.game_config, self.game_config.opt_params)
