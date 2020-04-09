from wit import Wit #https://github.com/wit-ai/pywit



class BotWit():
    client = None


    def __init__(self, access_token):
        self.client = Wit(access_token)


    def get_wit_response(self, message):
        if self.client is None:
            return

        resp = self.client.message(message)
        print(str(resp))
        return resp


    def get_intent(self, message):
        if self.client is None:
            return

        print("Tweet: "+ message)

        response = self.client.message(message)
        entities = response['entities']
        lost_intent = self.first_entity_value(entities, 'lost_intent')
        search_type = self.first_entity_value(entities, 'search_type')
        lost_adj = self.first_entity_value(entities, 'lost_adj')
        bot_name = self.first_entity_value(entities, 'bot_name')

        print(
            search_type + " ",
            lost_intent + " ",
            lost_adj
        )

        if bot_name:
            return True

        if search_type:
            if lost_intent or lost_adj:
                return True

        return False


    def first_entity_value(self, entities, entity):
        if entity not in entities:
            return None

        else:
            val = entities[entity][0]['value']
            if val:
                return val

            return None
