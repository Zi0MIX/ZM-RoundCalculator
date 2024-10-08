from dataclasses import dataclass
import numpy as np


COL, RES = "", ""
DEC = 3

# Time from "initial_blackscreen_passed" to "start_of_round" triggers
RND_WAIT_INITIAL = 8.25
# Time from "end_of_round" to "start_of_round"
RND_WAIT_END = 12.50
# Time from "end_of_round" to "between_round_over"
RND_WAIT_BETWEEN = RND_WAIT_END - 2.5
# Time difference between "start_of_round" trigger and new round number appearing
RND_BETWEEN_NUMBER_FLAG = 4.0

ZOMBIE_MAX_AI = 24
ZOMBIE_AI_PER_PLAYER = 6

# Perfect dog rounds, r5 then all 4 rounders
DOGS_PERFECT = [int(x) for x in range(256) if x % 4 == 1 and x > 4]
# 0.05 from ingame timing, code says 7 dot
DOGS_WAIT_START = 7.05      
DOGS_WAIT_END = 8
# Time between dog spawning to dog appearing on the map
DOGS_WAIT_TELEPORT = 1.5

MAP_LIST = ("zm_prototype", "zm_asylum", "zm_sumpf", "zm_factory", "zm_theater", "zm_pentagon", "zm_cosmodrome", "zm_coast", "zm_temple", "zm_moon", "zm_transit", "zm_nuked", "zm_highrise", "zm_prison", "zm_buried", "zm_tomb")
MAP_DOGS = ("zm_sumpf", "zm_factory", "zm_theater")


@dataclass
class ZombieRound:
    number: int
    players: int
    moon_teleports: int


    def __post_init__(self):
        self.get_network_frame()
        self.get_zombies()
        self.get_spawn_delay()
        self.get_round_time()
        self.get_zombie_health()


    def get_network_frame(self):
        self.network_frame = 0.05
        if self.players == 1:
            self.network_frame = 0.10

        return


    def get_round_spawn_delay(self, raw_delay: np.float32) -> np.float32:
        """Function uses Numpy to emulate Game Engine behavior\n
        Takes float32 `raw_delay` arugment and returns float32 value"""

        self.raw_spawn_delay = np.format_float_positional(raw_delay, min_digits=16)

        if raw_delay < 0.01:
            raw_delay = 0.01

        inside = str(raw_delay).split(".")

        if not len(inside[1]):
            real_decimals = ["0", "0"]
        elif len(inside[1]) == 1:
            real_decimals = [inside[1], "0"]
        else:
            real_decimals = [str(x) for x in inside[1]][:2]

            if len(inside[1]) > 2:
                # Round decimals outside of the scope in a normal way
                dec = reversed([int(x) for x in inside[1]][2:])
                # decimals = []
                remember = 0

                for x in dec:
                    x += remember
                    remember = 0

                    if x >= 5:
                        # decimals.append("0")
                        remember = 1
                    # else:
                    #     decimals.append("0")

                if remember:
                    real_decimals[1] = str(int(real_decimals[1]) + 1)
                    if real_decimals[1] == "10":
                        real_decimals[0] = str(int(real_decimals[0]) + 1)
                        real_decimals[1] = "0"

        # Round decimals in the scope to 0.05 following GSC way
        if real_decimals[1] in ("0", "1", "2"):
            real_decimals[1] = "0"
        elif real_decimals[1] in ("3", "4", "5", "6", "7"):
            real_decimals[1] = "5"
        else:
            real_decimals[1] = "0"
            real_decimals[0] = str(int(real_decimals[0]) + 1)

            if real_decimals[0] == "10":
                real_decimals[0] = "0"
                inside[0] = str(int(inside[0]) + 1)

        inside[1] = "".join(real_decimals)
        # print(f"{inside} / original: {str(self.raw_spawn_delay).split('.')}")

        return np.float32(".".join(inside))


    def get_spawn_delay(self):
        """Function uses Numpy to emulate Game Engine behavior"""
        self.zombie_spawn_delay = np.float32(2.0)
        self.raw_spawn_delay = np.float32(2.0)

        if get_args("remix"):
            self.zombie_spawn_delay = 1.0
            self.raw_spawn_delay = 1.0
        if get_args("waw_spawnrate"):
            self.zombie_spawn_delay = 3.0
            self.raw_spawn_delay = 3.0

        if self.number > 1:
            for _ in range(1, self.number + (self.moon_teleports * 2)):
                self.zombie_spawn_delay *= np.float32(0.95)

            self.zombie_spawn_delay = self.get_round_spawn_delay(self.zombie_spawn_delay)

            if self.zombie_spawn_delay < 0.1:
                self.zombie_spawn_delay = np.float32(0.1)

        self.zombie_spawn_delay = round(float(self.zombie_spawn_delay), 2)

        return


    def get_zombies(self):
        multiplier = self.number / 5
        if multiplier < 1:
            multiplier = 1.0
        elif self.number >= 10:
            multiplier *= (self.number * 0.15)

        if self.players == 1:
            temp = int(ZOMBIE_MAX_AI + (0.5 * ZOMBIE_AI_PER_PLAYER * multiplier))
        else:
            temp = int(ZOMBIE_MAX_AI + ((self.players - 1) * ZOMBIE_AI_PER_PLAYER * multiplier))

        self.zombies = temp
        if self.number < 2:
            self.zombies = int(temp * 0.25)
        elif self.number < 3:
            self.zombies = int(temp * 0.3)
        elif self.number < 4:
            self.zombies = int(temp * 0.5)
        elif self.number < 5:
            self.zombies = int(temp * 0.7)
        elif self.number < 6:
            self.zombies = int(temp * 0.9)

        self.hordes = round(self.zombies / 24, 2)

        if get_args("waw_spawnrate") and self.players == 1 and self.zombies > 24:
            self.zombies = 24

        return


    def extract_decimals(self):
        dec = "0"
        # '> 0' could result in 00000001 triggering the expression
        if int(str(self.raw_time).split(".")[1]) >= 1:
            dec = str(self.raw_time).split(".")[1][:3]

        while len(dec) < DEC:
            dec += "0"
        self.decimals = dec

        return


    def get_round_time(self):
        delay = self.zombie_spawn_delay + self.network_frame
        self.raw_time = (self.zombies * delay) - delay
        self.round_time = round(self.raw_time, 2)

        # self.extract_decimals()

        return


    def get_zombie_health(self):
        """Function uses Numpy to emulate Game Engine behavior"""

        self.is_insta_round = False
        self.health = np.int32(150)

        for r in range(2, self.number + 1):
            if r < 10:
                self.health += 100
            else:
                self.health += np.int32(np.float32(self.health) * np.float32(0.1))

        if (self.health <= np.int32(150)) and (self.number > 1):
            self.is_insta_round = True

            # print(f"DEV: Round: {r} / Health: {self.health}")

        return


@dataclass
class DogRound(ZombieRound):
    special_rounds: int


    def __post_init__(self):
        self.get_network_frame()
        self.get_dogs()
        self.get_teleport_time()
        self.get_dog_spawn_delay()
        self.get_total_delay()
        self.round_up()


    def get_dogs(self):
        self.dogs = self.players * 8

        if self.special_rounds < 3:
            self.dogs = self.players * 6

        return


    def get_teleport_time(self):
        # Seems to be the best indication of representing spawncap accurately, at least in case of solo when comparing to actual gameplay
        self.teleport_time = DOGS_WAIT_TELEPORT * (self.dogs / (2 * self.players))
        return


    def get_dog_spawn_delay(self):
        self.dog_spawn_delay = 1.50

        if self.special_rounds == 1:
            self.dog_spawn_delay = 3.00
        elif self.special_rounds == 2:
            self.dog_spawn_delay = 2.50
        elif self.special_rounds == 3:
            self.dog_spawn_delay = 2.00

        return


    def get_total_delay(self):
        self.raw_time = 0
        self.delays = []
        for i in range(1, self.dogs):
            delay = self.get_round_spawn_delay(self.dog_spawn_delay - (i / self.dogs))

            self.raw_time += delay
            self.delays.append(delay.item())

        self.raw_time = round(self.raw_time, 2)


    def add_teleport_time(self):
        # Call if dog teleport time should be added for each dog on class level
        self.raw_time += self.teleport_time
        return


    def round_up(self):
        # round_wait() function clocks every .5 seconds
        time_in_ms = round(self.raw_time * 1000)
        if not time_in_ms % 500:
            self.round_time = self.raw_time
            return

        self.round_time = ((time_in_ms - (time_in_ms % 500)) + 500) / 1000
        return
    

@dataclass
class PrenadesRound(ZombieRound):
    nade_type: str
    radius: float = None
    extra_damage: int = None


    def __post_init__(self):
        self.explosives_handler()


    def get_nadeconfig(self) -> dict:
        nadeconfigs = {
            "frag": {
                "max_radius": np.float32(256.0),
                "min_radius": np.float32(0.0),
                "max_damage": np.int32(300),
                "min_damage": np.int32(75),
                "damage_extra_max": np.int32(200),
                "damage_extra_min": np.int32(100),
            },
            "german": {
                "max_radius": np.float32(256.0),
                "min_radius": np.float32(0.0),
                "max_damage": np.int32(200),
                "min_damage": np.int32(50),
                "damage_extra_max": np.int32(200),
                "damage_extra_min": np.int32(100),
            },
            "semtex": {
                "max_radius": np.float32(256.0),
                "min_radius": np.float32(0.0),
                "max_damage": np.int32(300),
                "min_damage": np.int32(55),
                "damage_extra_max": np.int32(200),
                "damage_extra_min": np.int32(100),
            },
        }

        return nadeconfigs[self.nade_type]
    

    def get_bmx_damage(self) -> np.int32:
        if self.nade_type == "frag":
            return np.int32(np.float32(-0.880) * np.float32(self.radius) + np.int32(300))
        elif self.nade_type == "german":
            return np.int32(np.float32(-0.585) * np.float32(self.radius) + np.int32(200))
        elif self.nade_type == "semtex":
            return np.int32(np.float32(-0.958) * np.float32(self.radius) + np.int32(300))
        else:
            raise Exception(f"Could not set BMX damage value for nade type {self.nade_type}")


    def explosives_handler(self):
        """Function uses Numpy to emulate Game Engine behavior.\n
        Available nade types are `frag`, `german`, `semtex`"""

        if not isinstance(self.radius, float):
            raise Exception(f"Wrong argument type passed to 'radius_override'. Expected '{type(float())}', received '{type(self.radius)}'")

        nadecfg = self.get_nadeconfig()

        # Get average radius or else pickup override value. Important to pass float to the function call
        if self.radius is None:
            self.radius = np.float32((nadecfg["max_radius"] + nadecfg["min_radius"]) / 2)
        else:
            self.radius = np.float32(self.radius)

        # It has to wait until radius is defined
        bmx_damage = self.get_bmx_damage()

        # Get average extra damage or else pickup override value
        if self.extra_damage is None:
            self.extra_damage = np.int32((nadecfg["damage_extra_max"] + nadecfg["damage_extra_min"]) / 2) + np.int32(self.number)
        else:
            self.extra_damage = np.int32(self.extra_damage) + np.int32(self.number)

        self.nade_damage = np.int32(nadecfg["bmx_damage"] + self.extra_damage)

        current_health = np.int32(self.health)

        nades = np.int32(0)

        # Deal with bigger numbers for high rounds
        # 400_000 and 450_000 are the fastest for computation
        number_of_nades = np.int32(400_000) // self.nade_damage
        damage = number_of_nades * self.nade_damage
        while current_health > np.int32(450_000):
            current_health -= damage
            nades += number_of_nades
            # print(f"DEV: nades: {nades} / number_of_nades: {number_of_nades} / current_health: {current_health}")

        # Get exact number when number is already low
        while self.nade_damage / current_health * np.int32(100) < np.int32(10) and current_health > np.int32(150):
            # print(f"DEV: percent: {self.nade_damage / current_health * 100}% / current_health: {current_health}")
            nades += 1
            current_health -= self.nade_damage

        self.prenades = nades

        # print(f"DEV: Bmx damage: {bmx_damage}")
        # print(f"DEV: Nade damage: {self.nade_damage}")
        # print(f"DEV: Prenades on {self.number}: {self.prenades}")


def save_results_locally(to_save: list, path_override: str = "") -> None:
    from os.path import join
    from time import localtime, time
    try:
        import PySimpleGUI as sg
    except ModuleNotFoundError:
        sg = None

    # Avoid the rare situation where this is called from API and 'CYA' is undefined
    try:
        CYA
    except NameError:
        CYA = ""

    output = "\n".join(to_save)

    if path_override:
        path = path_override
    elif sg is None:
        print(f"{CYA}Enter path to where you want to save the file in{RES}")
        path = str(input("> "))
    else:
        while True:
            save_folder = sg.popup_get_folder("Save as: ", keep_on_top=True)

            if save_folder is None:
                print("Cancelled saving results.")
                return

            path = save_folder
            break

    t = localtime(time())
    a_filename = f"zm_round_calculator_{str(t[0]).zfill(4)}-{str(t[1]).zfill(2)}-{str(t[2]).zfill(2)}_{str(t[3]).zfill(2)}-{str(t[4]).zfill(2)}-{str(t[5]).zfill(2)}.txt"
    with open(join(path, a_filename), "w", encoding="utf-8") as newfile:
        newfile.write(output)

    return


def load_apiconfig():
    """Load a dictionary to global `APICONFIG`"""
    from os.path import join, dirname, abspath
    from json import load

    global APICONFIG
    try:
        path = join(dirname(abspath(__file__)), "config.json")
        with open(path, "r", encoding="utf-8") as rawcfg:
            api_cfg = load(rawcfg)
        APICONFIG = api_cfg
    except:
        APICONFIG = None

    return


def get_apiconfig(key: str = "") -> dict | None:
    try:
        APICONFIG
    except (NameError, UnboundLocalError):
        load_apiconfig()

    if isinstance(APICONFIG, dict) and key:
        return APICONFIG["api"][key]
    elif isinstance(APICONFIG, dict):
        return APICONFIG["api"]
    return APICONFIG


def load_args():
    """Load a dictionary to global `ARGS`"""
    all_arguments = get_arguments()
    global ARGS
    ARGS = {}
    [ARGS.update({key: all_arguments[key]["default_state"]}) for key in all_arguments.keys()]
    return


def get_args(key: str = "") -> bool | None:
    if not key:
        return ARGS
    return ARGS[key]


def update_args(key: str, state: bool = None) -> None:
    if state is None:
        ARGS[key] = not ARGS[key]
    else:
        ARGS[key] = state
    return


def return_error(nolist: bool = False) -> dict | list[dict]:
    from traceback import format_exc

    if nolist:
        return {"type": "error", "message": str(format_exc())}
    return [{"type": "error", "message": str(format_exc())}]


def eval_argv(cli_in: list[str]) -> list:
    return cli_in[1:]


def get_answer_blueprint() -> dict:
    """Check outputs.MD for reference"""
    return {
        "type": "blueprint",
        "mod": "",
        "message": "",
        "round": 0,
        "players": 0,
        "zombies": 0,
        "hordes": 0.0,
        "time_output": "00:00",
        "special_average": 0.0,
        "spawnrate": 0.0,
        "raw_spawnrate": 0.0,
        "network_frame": 0.0,
        "map_name": "",
        "moon_teleports": 0,
        "class_content": {},
    }


def get_arguments() -> dict:
    default_arguments = {
        "break": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Break",
            "shortcode": "-b",
            "default_state": True,
            "exp": "Display an empty line between results."
        },
        "clear": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Clear output",
            "shortcode": "-c",
            "default_state": False,
            "exp": "Show only numeric output as oppose to complete sentences. Use for datasets."
        },
        "detailed": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Detailed",
            "shortcode": "-d",
            "default_state": False,
            "exp": "Show time in miliseconds instead of formatted string."
        },
        "even_time": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Even time",
            "shortcode": "-e",
            "default_state": False,
            "exp": "Time output always has 5 symbols."
        },
        "hordes": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Hordes",
            "shortcode": "-h",
            "default_state": False,
            "exp": "Show the amount of hordes instead of the amount of zombies in the output."
        },
        "insta_rounds": {
            "use_in_web": True,
            "require_map": True,
            "readable_name": "Insta Rounds",
            "shortcode": "-i",
            "default_state": True,
            "exp": "Add information about instakill rounds to the output."
        },
        "lower_time": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Lower Time",
            "shortcode": "-l",
            "default_state": False,
            "exp": "Change seconds rounding to go down instead of up."
        },
        "nodecimal": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Nodecimal",
            "shortcode": "-n",
            "default_state": True,
            "exp": "Show time without decimals."
        },
        "perfect_times": {
            "use_in_web": True,
            "require_map": True,
            "readable_name": "Perfect times",
            "shortcode": "-p",
            "default_state": False,
            "exp": "Instead of perfect round times, display perfect split times for choosen map."
        },
        "prenades": {
            "use_in_web": False,    # Arg is not yet usable
            "require_map": True,
            "readable_name": "Prenades",
            "shortcode": "-P",
            "default_state": False,
            "exp": "Instead of perfect round times, display amount of prenades."
        },
        "range": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Range",
            "shortcode": "-r",
            "default_state": False,
            "exp": "Show results for all rounds leading to selected number."
        },
        "remix": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Remix",
            "shortcode": "-x",
            "default_state": False,
            "exp": "Use spawn and zombie logic applied in 5and5s mod Remix."
        },
        "save": {
            "use_in_web": False,
            "require_map": False,
            "readable_name": "Save",
            "shortcode": "-v",
            "default_state": False,
            "exp": "Save output to text file."
        },
        "special_rounds": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Special rounds",
            "shortcode": "-S",
            "default_state": False,
            "exp": "Add own set of special rounds to perfect times predictor to maps that support it."
        },
        "speedrun_time": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Speedrun time",
            "shortcode": "-s",
            "default_state": False,
            "exp": "Show times accordingly to speedrun rules, round end is on number transition instead of when zombies start spawning."
        },
        "teleport_time": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Teleport time",
            "shortcode": "-t",
            "default_state": True,
            "exp": "Adds dog appearance time to perfect dog rounds accordingly to the pattern: 't * dogs / (2 * players))'"
        },
        "teleports": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "Moon teleports",
            "shortcode": "-m",
            "default_state": False,
            "exp": "Enable adding number of moon teleports to spawnrate calculation (web only, won't work with --range)"
        },
        "waw_spawnrate": {
            "use_in_web": True,
            "require_map": False,
            "readable_name": "World at War Spawnrate",
            "shortcode": "-w",
            "default_state": False,
            "exp": "Apply higher initial spawnrate value from WaW's maps Nacht, Verruckt and Shino."
        },
    }

    if isinstance(get_apiconfig(), dict):
        overrides = get_apiconfig("arg_overrides")
        for high_key in overrides.keys():
            # There is no validation for keys that can be replaced, hopefully there doesn't have to be
            for low_key in overrides[high_key].keys():
                default_arguments.update({high_key[low_key]: overrides[high_key[low_key]]})

    return default_arguments


def curate_arguments(provided_args: dict) -> dict:
    """Define new rules in the dict below.If argument `master` is different than it's default state, argument `slave` is set to it's default state.\nIf key `eval_true` is set to `True`, function checks if argument `master` is `True`, and if so it sets argument `slave` to `False`"""

    rules = {}
    if isinstance(get_apiconfig(), dict):
        rules = get_apiconfig("new_rules")

    rules.update({
        "1": {
            "master": "detailed",
            "slave": "nodecimals",
            "eval_true": True,
        },
        "2": {
            "master": "waw_spawnrate",
            "slave": "remix",
            "eval_true": True,
        },
        "3": {
            "master": "teleports",
            "slave": "range",
            "eval_true": True,
        },
        "4": {
            "master": "teleports",
            "slave": "perfect_times",
            "eval_true": True,
        },
    })

    defaults = get_arguments()

    registered_pairs = []

    for rule in rules.keys():
        master = rules[rule]["master"]
        slave = rules[rule]["slave"]

        # Ignore rules that repeat or contradict with already applied ones
        if [master, slave] in registered_pairs or [slave, master] in registered_pairs:
            continue

        registered_pairs.append([master, slave])

        if rules[rule]["eval_true"]:
            if provided_args[master]:
                provided_args[slave] = False
        else:
            if provided_args[master] != defaults[master]["default_state"]:
                provided_args[slave] = defaults[slave]["default_state"]

    return provided_args


def convert_arguments(list_of_args: list[str]) -> dict:
    converted = {}
    converted.update({"rounds": int(list_of_args[0])})
    converted.update({"players": int(list_of_args[1])})
    try:
        converted.update({"map_code": str(list_of_args[2])})
    except IndexError:
        converted.update({"map_code": "unspecified"})
    # We set arguments to true, easier handling and CLI entry point can be processed fully, doesn't hurt
    converted.update({"arguments": True})
    # Currently not supported from CLI call
    converted.update({"spec_rounds": tuple()})

    default_arguments, arguments = get_arguments(), {}
    # Fill up dict with default values
    [arguments.update({a: default_arguments[a]["default_state"]}) for a in default_arguments.keys()]
    # Override arguments with opposite bool if argument is detected in input
    if len(list_of_args) > 3:
        [arguments.update({x: not default_arguments[x]["default_state"]}) for x in default_arguments.keys() if default_arguments[x]["shortcode"] in list_of_args[3:]]
    converted.update({"args": arguments})

    converted.update({"mods": []})
    if len(list_of_args) > 3:
        default_mods = get_mods()
        converted.update({"mods": [m for m in list_of_args[3:] if m in default_mods]})

    return converted


def get_mods() -> list:
    return ["-db", "-ddb", "-ps", "-rs", "-zc", "-ga", "-zh", "-ir", "-exc"]


def map_translator(map_code: str) -> str:

    if get_apiconfig() is not None and map_code in get_apiconfig("custom_translations").keys():
        return get_apiconfig("custom_translations")[map_code]

    if map_code == "zm_prototype":
        return "Nacht Der Untoten"
    if map_code == "zm_asylum":
        return "Verruckt"
    if map_code == "zm_sumpf":
        return "Shi No Numa"
    if map_code == "zm_factory":
        return "Der Riese"
    if map_code == "zm_theater":
        return "Kino Der Toten"
    if map_code == "zm_pentagon":
        return "FIVE"
    if map_code == "zm_cosmodrome":
        return "Ascension"
    if map_code == "zm_coast":
        return "Call of the Dead"
    if map_code == "zm_temple":
        return "Shangri-La"
    if map_code == "zm_moon":
        return "Moon"
    if map_code == "zm_transit":
        return "Tranzit"
    if map_code == "zm_nuked":
        return "Nuketown"
    if map_code == "zm_highrise":
        return "Die Rise"
    if map_code == "zm_prison":
        return "Mob of the Dead"
    if map_code == "zm_buried":
        return "Buried"
    if map_code == "zm_tomb":
        return "Origins"

    return map_code


def import_dogrounds() -> tuple:
    print(f"{CYA}Enter special rounds separated with space.{RES}")
    raw_special = str(input("> "))

    list_special = [int(x) for x in raw_special.split(" ") if x.isdigit()]
    if len(list_special):
        return tuple(list_special)
    return DOGS_PERFECT


def get_readable_time(round_time: float) -> str:
    h, m, s, ms = 0, 0, 0, int(round_time * 1000)

    while ms > 999:
        s += 1
        ms -= 1000
    while s > 59:
        m += 1
        s -= 60
    # Do not reduce minutes to hours if even_time is on
    if not get_args("even_time"):
        while m > 59:
            h += 1
            m -= 60

    dec = f".{str(ms).zfill(3)}"
    # Clear decimals and append a second, this way it's always rounding up
    if get_args("nodecimal") and not get_args("lower_time"):
        dec = ""
        s += 1
        if s > 59:
            m += 1
            s -= 60
            if m > 59:
                h += 1
                m -= 60
    # Otherwise just clear decimals, it then rounds down
    elif get_args("nodecimal"):
        dec = ""

    if not h and not m:
        new_time = f"{s}{dec} seconds"
    elif not h:
        new_time = f"{str(m).zfill(2)}:{str(s).zfill(2)}{dec}"
    else:
        new_time = f"{str(h).zfill(2)}:{str(m).zfill(2)}:{str(s).zfill(2)}{dec}"

    if get_args("even_time"):
        new_time = f"{str(m).zfill(2)}:{str(s).zfill(2)}"

    return new_time


def get_perfect_times(time_total: float, rnd: int, map_code: str, insta_round: bool, num_of_teleports: int) -> dict:

    a = get_answer_blueprint()
    a["type"] = "perfect_times"
    a["round"] = rnd
    a["raw_time"] = time_total
    a["map_name"] = map_translator(map_code)
    a["is_insta_round"] = insta_round
    a["moon_teleports"] = num_of_teleports

    split_adj = 0.0
    if get_args("speedrun_time"):
        split_adj = RND_BETWEEN_NUMBER_FLAG

    if get_args("detailed"):
        a["time_output"] = str(round(time_total * 1000)) + " ms"
    else:
        a["time_output"] = get_readable_time(time_total - split_adj)

    return a


def get_round_times(rnd: ZombieRound | DogRound) -> dict:

    a = get_answer_blueprint()
    a["type"] = "round_time"
    a["round"] = rnd.number
    a["players"] = rnd.players
    a["zombies"] = rnd.zombies
    a["hordes"] = rnd.hordes
    a["raw_time"] = rnd.raw_time
    a["spawnrate"] = rnd.zombie_spawn_delay
    a["raw_spawnrate"] = rnd.raw_spawn_delay
    a["network_frame"] = rnd.network_frame
    a["is_insta_round"] = rnd.is_insta_round
    a["moon_teleports"] = rnd.moon_teleports
    a["class_content"] = vars(rnd)

    split_adj = 0
    if get_args("speedrun_time"):
        split_adj = RND_BETWEEN_NUMBER_FLAG

    if get_args("detailed"):
        a["time_output"] = str(round(rnd.round_time * 1000)) + " ms"
    else:
        a["time_output"] = get_readable_time(rnd.round_time - split_adj)

    return a


def calculator_custom(rnd: int, players: int, mods: list[str], moon_teleports: int) -> list[dict]:
    calc_result = []
    single_iteration = False
    for r in range(1, rnd + 1):
        zm_round = ZombieRound(r, players, moon_teleports=moon_teleports)
        dog_round = DogRound(r, players, moon_teleports, r)

        a = get_answer_blueprint()
        a["type"] = "mod"
        a["round"] = r
        a["players"] = players
        a["raw_spawnrate"] = zm_round.raw_spawn_delay
        a["spawnrate"] = zm_round.zombie_spawn_delay
        a["zombies"] = zm_round.zombies
        a["health"] = zm_round.health
        a["moon_teleports"] = zm_round.moon_teleports
        a["class_content"] = vars(zm_round)
        a["message"] = ""

        if "-exc" in mods:
            raise Exception("This is a test exception")
        elif "-ga" in mods:
            rgs = get_arguments()
            a["mod"] = "-ga"
            a["message"] = "\n".join([f"{rgs[r]['shortcode']}: {rgs[r]['exp']}" for r in rgs.keys()])
            single_iteration = True
        elif "-ir" in mods:
            a["mod"] = "-ir"
            if zm_round.is_insta_round:
                a["message"] = f"Round {zm_round.number} is an insta-kill round. Zombie health: {zm_round.health}"
            else:
                continue
        elif "-rs" in mods:
            a["mod"] = "-rs"
            a["message"] = str(a["raw_spawnrate"])
        elif "-ps" in mods:
            a["mod"] = "-ps"
            a["message"] = str(a["spawnrate"])
        elif "-zc" in mods:
            a["mod"] = "-zc"
            a["message"] = str(a["zombies"])
        elif "-zh" in mods:
            a["mod"] = "-zh"
            a["message"] = str(a["health"])
        elif "-db" in mods:
            a["mod"] = "-db"
            a["message"] = str(a["class_content"])
        elif "-ddb" in mods:
            a["mod"] = "-ddb"
            a["class_content"] = vars(dog_round)
            a["message"] = str(a["class_content"])

        calc_result.append(a)

        if single_iteration:
            break

    return calc_result


def calculator_handler(json_input: dict = None):

    # Take input if standalone app
    if json_input is None:
        raw_input = input("> ").lower()
        raw_input = raw_input.split(" ")

        if not isinstance(raw_input, list) or len(raw_input) < 2:
            raise ValueError("Wrong data input")
        rnd, players = int(raw_input[0]), int(raw_input[1])

        use_arguments = len(raw_input) > 2
    # Assign variables from json otherwise
    else:
        rnd, players, map_code = int(json_input["rounds"]), int(json_input["players"]), str(json_input["map_code"])
        # try/except clause supports transition between keys, remove later
        try:
            use_arguments = json_input["arguments"] or len(json_input["mods"])
        except KeyError:
            use_arguments = json_input["use_arguments"] or len(json_input["mods"])

    all_arguments = get_arguments()
    load_args()

    # Define state of arguments
    if json_input is None:
        selected_arguments = raw_input[2:]
        for key in get_args().keys():
            if all_arguments[key]["shortcode"] in selected_arguments:
                update_args(key)
    else:
        for key in get_args().keys():
            try:
                update_args(key, json_input["args"][key])
            # The default state of the argument is already established, the error can be ignored
            except KeyError:
                continue

    teleport_rnd_offset = 0
    # Pull teleports only if it's toggled on, range is not used and we're in api mode
    if get_args("teleports") and not get_args("range") and isinstance(json_input, dict):
        teleport_rnd_offset = int(json_input["teleports"])

    # We do not process all the argument logic if arguments are not defined
    result = ZombieRound(rnd, players, teleport_rnd_offset)
    if not use_arguments:
        return [get_round_times(result)]

    # Define state of mods
    if json_input is None:
        selected_mods = raw_input[2:]
    else:
        selected_mods = json_input["mods"]
    mods = [mod for mod in get_mods() if mod in selected_mods]

    # If mods are selected, custom calculator function entered instead
    if len(mods):
        return calculator_custom(rnd, players, mods, teleport_rnd_offset)

    all_results = []

    # Process perfect splits
    if get_args("perfect_times"):

        if json_input is None:
            print("Enter map code (eg. zm_theater)")
            map_code = input("> ").lower()

        if map_code not in MAP_LIST:
            if json_input is None:
                print(f"Map {COL}{map_translator(map_code)}{RES} is not supported.")
            raise ValueError(f"{map_translator(map_code)} is not supported")

        time_total = RND_WAIT_INITIAL

        try:
            # Not map with dogs
            if map_code not in MAP_DOGS:
                set_dog_rounds = tuple()
            # Not specified special_rounds or is remix
            elif not get_args("special_rounds") or get_args("remix"):
                set_dog_rounds = DOGS_PERFECT
            # Not api mode or empty api entry provided -> take input
            elif not json_input or not len(json_input["spec_rounds"]):
                set_dog_rounds = import_dogrounds()
            # Take entry from api call
            else:
                set_dog_rounds = tuple(json_input["spec_rounds"])
        except KeyError:
            if not json_input:
                print("Warning: Key error dog rounds")
            set_dog_rounds = DOGS_PERFECT

        dog_rounds_average = 0.0
        if len(set_dog_rounds):
            from statistics import mean
            dog_rounds_average = round(mean(set_dog_rounds), 1)

        dog_rounds = 1
        for r in range(1, rnd):
            zm_round = ZombieRound(r, players, teleport_rnd_offset)
            dog_round = DogRound(r, players, teleport_rnd_offset, dog_rounds)

            # Handle arguments here
            if get_args("teleport_time"):
                dog_round.add_teleport_time()

            is_dog_round = r in set_dog_rounds

            if is_dog_round:
                dog_rounds += 1
                round_duration = DOGS_WAIT_START + DOGS_WAIT_TELEPORT + dog_round.round_time + DOGS_WAIT_END + RND_WAIT_END
                time_total += round_duration
            else:
                round_duration = zm_round.round_time + RND_WAIT_END
                time_total += round_duration

            if get_args("range"):
                remembered_dog_average = 0.0

                res = get_perfect_times(time_total, r + 1, map_code, zm_round.is_insta_round, teleport_rnd_offset)
                res["players"] = players
                res["class_content"] = vars(zm_round)
                res["special_average"] = remembered_dog_average
                if is_dog_round:
                    res["class_content"] = vars(dog_round)

                    # Get new average on each dog round
                    temp_dog_rounds = [d for d in set_dog_rounds if d <= r]
                    res["special_average"] = round(sum(temp_dog_rounds) / len(temp_dog_rounds), 1)
                    remembered_dog_average = res["special_average"]

                all_results.append(res)

        if not get_args("range"):
            res = get_perfect_times(time_total, rnd, map_code, zm_round.is_insta_round, teleport_rnd_offset)
            res["players"] = players
            res["class_content"] = vars(zm_round)
            res["special_average"] = dog_rounds_average
            if is_dog_round:
                res["class_content"] = vars(dog_round)
            all_results.append(res)

        return all_results

    if get_args("range"):
        all_results = [get_round_times(ZombieRound(r, players, teleport_rnd_offset)) for r in range (1, rnd)]
        return all_results

    return [get_round_times(ZombieRound(rnd, players, teleport_rnd_offset))]


def display_results(results: list[dict]) -> list[dict]:
    readable_results = []

    # If entered from error handler in api, args will not be defined, and they don't need to
    try:
        get_args()
    except (NameError, UnboundLocalError):
        load_args()

    for res in results:

        # Assemble print
        zm_word = "zombies"
        if res["type"] == "error":
            readable_result = f"An error occured, if your inputs are correct, please contact the creator and provide error message.\n{res['message']}"
            readable_results.append(readable_result)
            print(readable_result)

        elif res["type"] == "round_time":
            enemies = res["zombies"]
            if get_args("hordes"):
                zm_word = "hordes"
                enemies = res["hordes"]

            if get_args("clear"):
                readable_result = res["time_output"]
            else:
                readable_result = f"Round {COL}{res['round']}{RES} will spawn in {COL}{res['time_output']}{RES} and has {COL}{enemies}{RES} {zm_word}. (Spawnrate: {COL}{res['spawnrate']}{RES} / Network frame: {COL}{res['network_frame']}{RES})."

            readable_results.append(readable_result)
            print(readable_result)
            if get_args("break"):
                print()

        elif res["type"] == "perfect_times":
            if get_args("clear"):
                readable_result = res["time_output"]
            else:
                readable_result = f"Perfect time to round {COL}{res['round']}{RES} is {COL}{res['time_output']}{RES} on {COL}{res['map_name']}{RES}."

            readable_results.append(readable_result)
            print(readable_result)
            if get_args("break"):
                print()

        elif res["type"] == "mod":
            readable_result = res["message"]
            readable_results.append(readable_result)
            print(readable_result)

    readable_results = [str(st).replace(COL, "").replace(RES, "") for st in readable_results]

    if get_args("save"):
        save_results_locally(readable_results)

    return results


def main_app() -> None:
    import os
    from colorama import init, reinit, deinit

    os.system("cls")    # Bodge for colorama not working after compile
    init()              # Be aware, if colorama is not present this is outside of error handler
    print(f"Welcome in ZM Round Calculator {YEL}V3{RES} by Zi0")
    print(f"Source: '{CYA}https://github.com/Zi0MIX/ZM-RoundCalculator{RES}'")
    print(f"Check out web implementation of the calculator under '{CYA}https://zi0mix.github.io{RES}'")
    print("Enter round number and amount of players separated by spacebar, then optional arguments")
    print("Round and Players arguments are mandatory, others are optional. Check ARGUMENTS.MD on GitHub for info.")

    while True:
        try:
            reinit()
            result = calculator_handler(None)
            display_results(result)
            deinit()
        except Exception:
            display_results(return_error())


def main_api(arguments: dict | list, argv_trigger: bool = False) -> dict:

    try:
        own_print = True
        if not argv_trigger:
            own_print = False

        if isinstance(get_apiconfig(), dict):
            own_print = get_apiconfig("own_print")

        if argv_trigger:
            arguments = eval_argv(argv)

        if isinstance(arguments, list):
            arguments = convert_arguments(arguments)

        arguments["args"] = curate_arguments(arguments["args"])

        # Debug print
        # print(own_print)

        if own_print:
            return display_results(calculator_handler(arguments))
        return calculator_handler(arguments)

    except Exception:
        if own_print:
            return display_results(return_error())
        return return_error()


if __name__ == "__main__":
    from sys import argv

    # Avoid warning while calculating insta rounds
    np.seterr(over="ignore")
    # np.set_printoptions(precision=16, floatmode="fixed")

    if len(argv) > 1:
        main_api(argv, argv_trigger=True)
    else:
        from colorama import Fore
        # For output syntax highlighting use COL variable
        COL, RES = Fore.YELLOW, Fore.RESET
        YEL, GRE, RED, CYA = Fore.YELLOW, Fore.GREEN, Fore.RED, Fore.CYAN

        # Standalone app
        main_app()
