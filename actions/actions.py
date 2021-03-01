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

BASE_URL = 'http://localhost:3009/thesis_bot_backend/common/'

CHECK_BALANCE = BASE_URL + 'check_balance'
SET_BALANCE = BASE_URL + 'set_balance'
CHECK_AFFORDABILITY = BASE_URL + 'check_affordability'
ADD_TO_LIBRARY = BASE_URL + 'add_to_library'
REMOVE_FROM_LIBRARY = BASE_URL + 'remove_from_library'
SHOW_AVAILABLE_GAMES = BASE_URL + 'show_available_games'
SHOW_LIBRARY_GAMES = BASE_URL + 'show_library_games'
PURCHASE = BASE_URL + 'purchase'
ADD_BALANCE = BASE_URL + 'add_balance'


class ActionRemoveFromLibrary(Action):

  def name(self):
    return 'action_remove_game_from_library'

  async def run(self, dispatcher, tracker, domain):
    games_to_remove = pydash.map_(tracker.latest_message['entities'], 'value')
    games_in_library = tracker.get_slot('library_games')
    game_ids = []

    for game_to_remove in games_to_remove:
      for game_in_library in games_in_library:
        if(game_to_remove.lower() in game_in_library['name'].lower() and not (game_in_library['game_id'] in game_ids)):
          game_ids.append(game_in_library['game_id'])
          break
    print(game_ids)
    game_ids.append(-1)
    data = {
      "game_ids": game_ids
    }

    async with aiohttp.ClientSession() as session:
      async with session.post(REMOVE_FROM_LIBRARY, data=data) as resp:
        response = await resp.json()
        if(resp.status == 200):
          dispatcher.utter_message(template='utter_remove_from_library_success')
          if(len(response['library'])):
            return [SlotSet('library_games', response['library'])]
          else:
            return [SlotSet('library_games', None)]
        else:
          dispatcher.utter_message(template='utter_remove_from_library_failure')
          return []


class ActionIsCartAffordable(Action):

  def name(self):
    return 'action_is_cart_affordable'

  async def run(self, dispatcher, tracker, domain):
    all_available_games = tracker.get_slot('available_games')
    previously_in_cart = tracker.get_slot('shopping_cart')


    if(previously_in_cart):

      game_ids = []
      for cart_game in previously_in_cart:
        for available_game in all_available_games:
          if(available_game['name'] == cart_game):
            game_ids.append(available_game['game_id'])
            break

      if(len(game_ids)):

        game_ids.append(-1)  # For some reason if there is only one element in array, req.body.game_ids on the node.js backend gets a single string which is that element instead of the array itself...?? That's why I am adding a decoy -1.
        data = {
          "game_ids": game_ids
        }

        async with aiohttp.ClientSession() as session:
          async with session.get(CHECK_AFFORDABILITY, data=data) as resp:
            response = await resp.json()
            if(response['can_afford']):
              dispatcher.utter_message(
                template='utter_cart_affordable_yes',
                balance=response['balance'],
                total_cart_cost=response['cost']
              )
            else:
              dispatcher.utter_message(
                template='utter_cart_affordable_no',
                balance=response['balance'],
                total_cart_cost=response['cost'],
                shortage=response['shortage']
              )
            return [
              SlotSet('balance', response['balance']),
              SlotSet('total_cart_cost', response['cost']),
              SlotSet('shortage', response['shortage'])
            ]
      else:
        dispatcher.utter_message(template='utter_cart_is_empty')
        return []
    else:
      dispatcher.utter_message(template='utter_cart_is_empty')
      return []


class ActionRemoveEntireCart(Action):

  def name(self):
    return 'action_remove_all_from_cart'

  def run(self, dispatcher, tracker, domain):
    dispatcher.utter_message(template='utter_entire_cart_removed')
    return [SlotSet("shopping_cart", None)]


class ActionRemoveFromCart(Action):

  def name(self):
    return 'action_remove_from_cart'


  def run(self, dispatcher, tracker, domain):

    previously_in_cart = tracker.get_slot('shopping_cart');
    games_to_remove = []

    if(previously_in_cart):

      new_cart_games = [*previously_in_cart]
      games_to_remove = pydash.map_(tracker.latest_message['entities'], 'value')

      for game in games_to_remove:
        for current_cart_game in [*new_cart_games]:
          if(game in current_cart_game):
            new_cart_games.remove(current_cart_game)
      if(len(new_cart_games) == 0):
        dispatcher.utter_message(template='utter_cart_is_empty')
        return [SlotSet("shopping_cart", None)]
      else:
        dispatcher.utter_message(template="utter_removed_from_cart")
        return [SlotSet("shopping_cart", new_cart_games)]
    else:
      dispatcher.utter_message(template='utter_cart_is_empty')
      return []
    


class ActionShowCart(Action):
  def name(self):
    return "action_show_cart"

  async def run(self, dispatcher, tracker, domain):

    all_available_games = tracker.get_slot('available_games')
    previously_in_cart = tracker.get_slot('shopping_cart')

    result = []
    if(previously_in_cart):
      for game in previously_in_cart:
        for available_game in all_available_games:
          if(game == available_game['name']):
            result.append(game + ' (Price: ' + str(available_game['price']) + ')')
            break
      dispatcher.utter_message(text='\n'.join(result));
    else:
      dispatcher.utter_message(template='utter_cart_is_empty')
    return []


class ActionAddToCart(Action):

  def name(self):
    return "action_add_to_cart"

  async def run(self, dispatcher, tracker, domain):
    async with aiohttp.ClientSession() as session:
      async with session.get(SHOW_AVAILABLE_GAMES) as resp:
        result = await resp.json()

        available_games = pydash.map_(result, 'name')
        new_games_in_cart = pydash.map_(tracker.latest_message['entities'], 'value')
        new_cart_games = []

        previously_in_cart = tracker.get_slot('shopping_cart');

        if(previously_in_cart):
          new_cart_games = [*previously_in_cart]

        for new_game in new_games_in_cart:
          for game in available_games:
            if(new_game.lower() in game.lower() and game not in new_cart_games):
              new_cart_games.append(game)
              break
        
        dispatcher.utter_message(template='utter_added_to_cart')
        return [SlotSet("shopping_cart", new_cart_games)]

class ActionBuyCartItems(Action):
  
  def name(self):
    return 'action_buy_cart_items'

  async def run(self, dispatcher, tracker, domain):
    available_games = tracker.get_slot('available_games')
    currently_in_cart = tracker.get_slot('shopping_cart')
    if(not currently_in_cart or not len(currently_in_cart)):
      dispatcher.utter_message(template="utter_cart_is_empty")
      return [SlotSet("shopping_cart", None)]
    else:
      game_ids = []
      for game in currently_in_cart:
        for available_game in available_games:
          if(game == available_game['name']):
            game_ids.append(available_game['game_id'])
            break
      if(len(game_ids)):
        game_ids.append(-1)
        data = {
          'game_ids': game_ids
        }
        async with aiohttp.ClientSession() as session:
          async with session.post(PURCHASE, data = data) as resp:
            if(resp.status == 200):
              dispatcher.utter_message(template='utter_purchase_success')
              return [
                SlotSet("shopping_cart", None),
                SlotSet("balance", None)
              ]
            else:
              dispatcher.utter_message(template='utter_purchase_filure')
              return []
      else:
        dispatcher.utter_message(template="utter_cart_is_empty")
        return [SlotSet("shopping_cart", None)]

class ActionCheckBalance(Action):

  def name(self):
    return "action_check_balance"

  async def run(self, dispatcher, tracker, domain):
    async with aiohttp.ClientSession() as session:
      async with session.get(CHECK_BALANCE) as resp:
        result = await resp.json()
        dispatcher.utter_message(template="utter_balance", balance=result['balance'])
        return [SlotSet("balance", result['balance'])]


class ActionAddMoney(Action):

  def name(self):
    return "action_add_money"

  async def run(self, dispatcher, tracker, domain):
    amount = int(tracker.latest_message['entities'][0]['value'])
    data = {
      "amount": amount
    }
    async with aiohttp.ClientSession() as session:
      async with session.post(ADD_BALANCE, data = data) as resp:
        if(resp.status == 200):
          response = await resp.json()
          dispatcher.utter_message(template="utter_amount_added_success", balance=response['balance'], amount=response['amount'])
          return [
            SlotSet("balance", response['balance']),
            SlotSet("amount", None)
          ]
        else:
          dispatcher.utter_message(template="utter_amount_added_failure")
          return [
            SlotSet("balance", None),
            SlotSet("amount", None)
          ]


class ActionShowLibrary(Action):
  
  def name(self):
    return "action_show_library"
  
  async def run(self, dispatcher, tracker, domain):
    async with aiohttp.ClientSession() as session:
      async with session.get(SHOW_LIBRARY_GAMES) as resp:
        result = await resp.json()
        if(result['library'] and len(result['library'])):
          dispatcher.utter_message(text='\n'.join(pydash.map_(result['library'], 'name')))
          return [SlotSet("library_games", result['library'])]
        else:
          return [SlotSet("library_games", None)]



class ActionShowAvailableGames(Action):
  
  def name(self):
    return "action_show_available_games"

  async def run(self, dispatcher, tracker, domain):
    async with aiohttp.ClientSession() as session:
        async with session.get(SHOW_AVAILABLE_GAMES) as resp:
          result = await resp.json()
          dispatcher.utter_message(text='\n'.join(map(lambda game: game['name'] + ' (Price: ' + str(game['price']) + ')', result)))
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
