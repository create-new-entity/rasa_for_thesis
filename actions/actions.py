# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
import aiohttp
import pydash

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

BASE_URL = 'http://localhost:3009/thesis_bot_backend/'

CHECK_BALANCE = BASE_URL + 'common/check_balance'
SET_BALANCE = BASE_URL + 'common/set_balance'
CHECK_AFFORDABILITY = BASE_URL + 'common/check_affordability'
ADD_TO_LIBRARY = BASE_URL + 'common/add_to_library'
REMOVE_FROM_LIBRARY = BASE_URL + 'common/remove_from_library'
SHOW_AVAILABLE_GAMES = BASE_URL + 'common/show_available_games'


class ActionShowCart(Action):
  def name(self):
    return "action_show_cart"

  async def run(self, dispatcher, tracker, domain):
    previously_in_cart = tracker.get_slot('shopping_cart');
    if(previously_in_cart):
      dispatcher.utter_message(text='\n'.join(previously_in_cart));
    else:
      dispatcher.utter_message(template='utter_cart_is_empty')
    return []


class ActionAddToCart(Action):

  def name(self):
    return "action_add_to_cart"

  async def run(self, dispatcher, tracker, domain):
    # print(next(tracker.get_latest_entity_values("game")))
    # print(next(tracker.get_latest_entity_values("game")))
    # print(next(tracker.get_latest_entity_values("game")))
    async with aiohttp.ClientSession() as session:
      async with session.get(SHOW_AVAILABLE_GAMES) as resp:
        result = await resp.json()

        available_games = pydash.map_(result, 'name')
        new_games_in_cart = pydash.map_(tracker.latest_message['entities'], 'value')
        new_cart_games = []

        previously_in_cart = tracker.get_slot('shopping_cart');

        print()
        print()
        print('Previously in cart:')
        print(previously_in_cart)
        print()
        print()

        if(previously_in_cart):
          new_cart_games = [*previously_in_cart]

        for new_game in new_games_in_cart:
          for game in available_games:
            if(new_game in game and game not in new_cart_games):
              new_cart_games.append(game)
              break
        
        print(tracker.latest_message['entities'])
        dispatcher.utter_message(text="Will see")
        return [SlotSet("shopping_cart", new_cart_games)]

class ActionCheckBalance(Action):

  def name(self):
    return "action_check_balance"

  async def run(self, dispatcher, tracker, domain):
    async with aiohttp.ClientSession() as session:
      async with session.get(CHECK_BALANCE) as resp:
        result = await resp.json()
        dispatcher.utter_message(template="utter_balance", balance=result['balance'])
    return []


class ActionShowLibrary(Action):
  
  def name(self):
    return "action_show_library"
  
  def run(self, dispatcher, tracker, domain):

    dispatcher.utter_message(text="Will see")

    return []



class ActionShowAvailableGames(Action):
  
  def name(self):
    return "action_show_available_games"

  async def run(self, dispatcher, tracker, domain):
    async with aiohttp.ClientSession() as session:
        async with session.get(SHOW_AVAILABLE_GAMES) as resp:
          result = await resp.json()
          dispatcher.utter_message(text='\n'.join(pydash.map_(result, 'name')))
          return [SlotSet("available_games", result)]

#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
