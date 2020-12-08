from wit import Wit #https://github.com/wit-ai/pywit



class BotWit():

    def __init__(self, access_token):
        self.client = Wit(access_token)


    def get_wit_response(self, message):
        # Unused method on current class and on bot.py
        # print(str(self.client.message(message)))
        return self.client.message(message) if self.client else None


    def get_intent(self, message):
        if self.client is None:
            return

        #print("Tweet: "+ message)
        response = self.get_wit_response(message)
        entities = response.get("entities") # What would happen if this is a None returned by the method ?
        lost_intent = self.first_entity_value(entities, "lost_intent")
        search_type = self.first_entity_value(entities, "search_type")
        lost_adj = self.first_entity_value(entities, "lost_adj")
        bot_name = self.first_entity_value(entities, "bot_name")
        #print(search_type," ",lost_intent," ",lost_adj)
        if bot_name: #Assert that bot_name doesn't return an empty data structure
            return True

        if search_type:
           # return lost_intent or lost_adj
            if lost_intent or lost_adj:
                return True

        return False


    def first_entity_value(self, entities, entity):
        if entity not in entities:
            return None

        return entities[entity][0]['value'] or None