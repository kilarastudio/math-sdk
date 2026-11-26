"""Cluster pays evaluated through the footprint grid."""

from src.executables.executables import Executables
from src.calculations.cluster import Cluster


class GameCalculations(Executables):
    """Game specific calculations for Floppy Rabbit."""

    def evaluate_clusters_with_footprints(self) -> dict:
        """Pay every cluster of 5+ like symbols, multiplied by the sum of the footprints under it.

        A cluster with no footprint under it pays 1x.
        """
        clusters = Cluster.get_clusters(self.board, "wild")
        return_data = {"totalWin": 0, "wins": []}
        total_win = 0.0
        for sym in clusters:
            for cluster in clusters[sym]:
                size = len(cluster)
                if (size, sym) not in self.config.paytable:
                    continue
                footprint_sum = sum(self.footprints[reel][row] for reel, row in cluster)
                cluster_mult = max(footprint_sum, 1)
                base_win = self.config.paytable[(size, sym)]
                win = base_win * cluster_mult
                total_win += win
                positions = [{"reel": reel, "row": row} for reel, row in cluster]
                overlay = Cluster.get_central_cluster_position(positions)
                return_data["wins"].append(
                    {
                        "symbol": sym,
                        "clusterSize": size,
                        "win": win,
                        "positions": positions,
                        "meta": {
                            "globalMult": 1,
                            "clusterMult": cluster_mult,
                            "winWithoutMult": base_win,
                            "overlay": {"reel": overlay[0], "row": overlay[1]},
                        },
                    }
                )
                for reel, row in cluster:
                    self.board[reel][row].explode = True
        return_data["totalWin"] = total_win
        return return_data
