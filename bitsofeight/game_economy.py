import random


class GameResource(object):
    """Simple container class for the in-game resources"""
    def __init__(self):
        # set some initial amounts
        self.res = {
            'gold':    {'amount': 10,
                        'maint':  1,
                        'income': 0,
                        },

            'wood':    {'amount': 50,
                        'maint':  1,
                        'income': 0,
                        },

            'iron':    {'amount': 50,
                        'maint':  1,
                        'income': 0,
                        },

            'rum':     {'amount': 50,
                        'maint':  1,
                        'income': 0,
                        },

            'food':    {'amount': 50,
                        'maint':  1,
                        'income': 0,
                        },

            'water':   {'amount': 50,
                        'maint':  1,
                        'income': 0,
                        },

            # implicitly includes powder, unless we want to make powder kegs a weapon
            'shot':   {'amount':  20,
                       'maint':   0,
                       'income':  0,
                       },

            'cannon': {'amount': 2},
        }

class GameEvents(object):
    def __init__(self):
        self.res = GameResource().res

    def daily_tick(self):
        '''Decrement the stocks of resources once per 'day' '''
        for item, i in self.res.iteritems():
            i['amount'] = i['amount'] + i['income'] - i['maint']

        if random.random() < 0.01:  # life is harsh on the high seas
            self.poisoned_food()

    def shot_fired(self):
        self.res['shot'] -= 1
        if random.random() < 0.05:  # cannons are prone to destruction
            # TODO - dispatch a "you've lost a cannon" event
            self.res['cannon']['amount'] -= 1

    def build_cannon(self):
        # only in base!
        if self.res['cannon']['amount'] < 10:
            self.res['iron']['amount'] -= 50
            self.res['wood']['amount'] -= 10
            # TODO - dispatch "tink tink" building sound
            self.res['cannon']['amount'] += 1
        else:
            # TODO - "too many cannons!"
            pass

    def poisoned_food(self):
        # TODO - dispatch a "spoiled food" event, but not in combat
        self.res['food']['amount'] = int(self.res['food']['amount']) / 2

    def buy_wood(self):
        # TODO - dispatch coins sound
        # lumber is cheap
        self.res['gold']['amount'] -= 1
        self.res['wood']['amount'] += 10

    def buy_iron(self):
        # TODO - dispatch coins sound
        # iron is not cheap
        self.res['gold']['amount'] -= 1
        self.res['iron']['amount'] += 1


