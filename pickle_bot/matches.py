from enum import auto, Enum
from random import sample, shuffle


class CourtType(Enum):
    DOUBLES = auto()
    SINGLES = auto()

    def size(self):
        match self:
            case self.DOUBLES:
                return 4
            case self.SINGLES:
                return 2


class Match:
    def __init__(self, court_type: CourtType, players: [str]):
        assert len(players) == court_type.size(), "Court must have correct number of players"
        self.court_type = court_type
        self.players = players
        shuffle(self.players)

    def __str__(self):
        match self.court_type:
            case CourtType.DOUBLES:
                return (
                    f"{self.players[0]} and {self.players[1]}"
                    " VS "
                    f"{self.players[2]} and {self.players[3]}"
                )
            case CourtType.SINGLES:
                return f"{self.players[0]} VS {self.players[1]}"


class NotEnoughPlayersError(Exception):
    def __init__(self, singles: int, doubles: int, players: [str]):
        message = (
            f"Can't make matches with {len(players)} < {singles} * {CourtType.SINGLES.size()} +"
            f" {doubles} * {CourtType.DOUBLES.size()}"
        )
        super().__init__(message)


def get_random_matches(singles: int, doubles: int, players: [str]) -> [Match]:
    court_types = [CourtType.SINGLES] * singles + [CourtType.DOUBLES] * doubles
    if len(players) < sum(court_type.size() for court_type in court_types):
        raise NotEnoughPlayersError(singles, doubles, players)
    matches = []
    remaining_players = players
    for court_type in court_types:
        match_players = sample(remaining_players, court_type.size())
        matches.append(Match(court_type, match_players))
        remaining_players = [player for player in remaining_players if player not in match_players]
    return matches
