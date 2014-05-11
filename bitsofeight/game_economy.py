import random

class GameResource(object):
    '''Simple container class for the in-game resources'''
    def __init__(self):
        # set some initial amounts
        self.wood   = 50
        self.iron   = 50
        self.rum    = 50
        self.food   = 50
        self.water  = 50
        self.shot   = 20
        self.cannon = 2

        # the default just running per day costs you
        self.wood_daily_maint  = 1
        self.iron_daily_maint  = 1
        self.rum_daily_maint   = 1
        self.food_daily_maint  = 1
        self.water_daily_maint = 1
        self.shot_daily_maint  = 0 # might use this for some random effects

    def daily_tick(self):
        '''Decrement the stocks of resources once per day'''
        self.wood  -= self.wood_daily_maint
        self.iron  -= self.iron_daily_maint
        self.rum   -= self.rum_daily_maint
        self.food  -= self.food_daily_maint
        self.water -= self.daily_shot_maint
        self.shot  -= self.shot_daily_maint

    def shot_fired(self):
        self.shot -= 1
        if random.random() < 0.05:
            # TODO - dispatch a "you've lost a cannon" event
            self.cannon -= 1

    def build_cannon(self):
        if self.cannon < 10:
            self.iron -= 50
            self.wood -= 10
            self.cannon += 1
        else:
            # TODO - "too many cannons!"
            pass

    def poisoned_food(self):
        # TODO - dispatch a "spoiled food" event, but not in combat
        self.food = int(self.food) / 2

