from colorama import Fore


COL = Fore.YELLOW
RES = Fore.RESET
DEC = 3

RND_WAIT_INITIAL = 8.25         # From initial_blackscreen_passed to start_of_round
RND_WAIT_BETWEEN = 12.50
RND_BETWEEN_NUMBER_FLAG = 4.0   # Verify the value

ZOMBIE_MAX_AI = 24
ZOMBIE_AI_PER_PLAYER = 6

DOGS_PERFECT = [int(x) for x in range(256) if x % 4 == 1 and x > 4]     # 5 then all 4 rounders
DOGS_WAIT_START = 7
DOGS_WAIT_END = 8

MAP_LIST = ("zm_prototype", "zm_asylum", "zm_sumpf", "zm_factory", "zm_theater", "zm_pentagon", "zm_cosmodrome", "zm_coast", "zm_temple", "zm_moon", "zm_transit", "zm_nuked", "zm_highrise", "zm_prison", "zm_buried", "zm_tomb")