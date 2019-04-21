# -*- coding: utf-8 -*-

import logging
import requests
import six
import random
import json
from operator import itemgetter

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractResponseInterceptor, AbstractRequestInterceptor)
from ask_sdk_core.utils import is_intent_name, is_request_type

from typing import Union, Dict, Any, List
from ask_sdk_model.dialog import (
    ElicitSlotDirective, DelegateDirective)
from ask_sdk_model import (
    Response, IntentRequest, DialogState, SlotConfirmationStatus, Slot)
from ask_sdk_model.slu.entityresolution import StatusCode

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Request Handler classes
class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for skill launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In LaunchRequestHandler")
        speech = ('<say-as interpret-as="interjection">Bonjour</say-as>! I can smell spring in the air! I am your personal fragrance advisor. '
                  'You can ask me for recommendations or learn what notes a fragrance contains.')
        reprompt = "How can I help you? Say \'fragrance advisor options\' to learn what I can do."
        handler_input.response_builder.speak(speech).ask(reprompt)
        return handler_input.response_builder.response

class HandleMakerIntent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("MakerIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HandleMakerIntent")
        filled_slots = slot = handler_input.request_envelope.request.intent.slots
        slot_values = get_slot_values(filled_slots)

        try:
            brand = get_brand(
                base_url=scentsee_api["base_url"], path=scentsee_api["name"], slot_values=slot_values)

            if brand:
                speech = ("{} "             
                          "was made by {}".format(
                    slot_values["perfume"]["resolved"],
                   brand)
                )
            else:
                speech = ("I am sorry I could not find any info on "
                          "{} ".format(
                    slot_values["perfume"]["resolved"])
                )
        except Exception as e:
            speech = ("I am really sorry. I am unable to access part of my "
                      "memory. Please try again later")
            logger.info("Intent: {}: message: {}".format(
                handler_input.request_envelope.request.intent.name, str(e)))

        reprompt = "What else can I help you with?"
        handler_input.response_builder.speak(speech).ask(reprompt)

        return handler_input.response_builder.response

class HandleBaseNotesIntent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("BaseNotesIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HandleBaseNotesIntent")
        filled_slots = slot = handler_input.request_envelope.request.intent.slots
        slot_values = get_slot_values(filled_slots)

        try:
            base_notes = get_base_notes(
                base_url=scentsee_api["base_url"], name_call=scentsee_api["name"], reco_call=scentsee_api["reco_by_id"], slot_values=slot_values)

            if base_notes and base_notes["strongest"] and base_notes["rest"] :
                speech = ("{} by {} "             
                          "mostly contains {} notes "
                        "with some {} notes present".format(
                    slot_values["perfume"]["resolved"],
                    base_notes["brand"],
                    base_notes["strongest"],
                    base_notes["rest"])
                )
            elif base_notes and base_notes["strongest"] and not base_notes["rest"] :
                speech = ("{} by {} "
                          "contains {} notes".format(
                    slot_values["perfume"]["resolved"],
                    base_notes["brand"],
                    base_notes["strongest"])
                )
            else:
                speech = ("I am sorry I could not find any info on "
                          "{} ".format(
                    slot_values["perfume"]["resolved"])
                )
        except Exception as e:
            speech = ("I am really sorry. I am unable to access part of my "
                      "memory. Please try again later")
            logger.info("Intent: {}: message: {}".format(
                handler_input.request_envelope.request.intent.name, str(e)))

        reprompt = "What else can I help you with?"
        handler_input.response_builder.speak(speech).ask(reprompt)

        return handler_input.response_builder.response

class HandleRecommendLikeIntent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("RecommendLikeIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HandleRecommendLikeIntent")
        filled_slots = slot = handler_input.request_envelope.request.intent.slots
        slot_values = get_slot_values(filled_slots)

        try:
            recos = get_recos_like_name(
                base_url=scentsee_api["base_url"], name_call=scentsee_api["name"], reco_call=scentsee_api["reco_by_id"], slot_values=slot_values)

            if recos["recos"] :
                speech = ("Since you like {} by {} "             
                        "you might also like: {}".format(
                    slot_values["perfume"]["resolved"],
                    recos["brand"],
                    recos["recos"])
                )
            else:
                speech = ("I am sorry I could not find any info on "
                          "{} ".format(
                    slot_values["perfume"]["resolved"])
                )
        except Exception as e:
            speech = ("I am really sorry. I am unable to access part of my "
                      "memory. Please try again later")
            logger.info("Intent: {}: message: {}".format(
                handler_input.request_envelope.request.intent.name, str(e)))

        reprompt = "What else can I help you with?"
        handler_input.response_builder.speak(speech).ask(reprompt)

        return handler_input.response_builder.response

class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for handling fallback intent.

     2018-May-01: AMAZON.FallackIntent is only currently available in
     en-US locale. This handler will not be triggered except in that
     locale, so it can be safely deployed for any locale."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = ("I'm sorry Pet Match can't help you with that. I can help "
                  "find the perfect dog for you. What are two things you're "
                  "looking for in a dog?")
        reprompt = "What size and temperament are you looking for in a dog?"
        handler_input.response_builder.speak(speech).ask(reprompt)
        return handler_input.response_builder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for help intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HelpIntentHandler")
        speech = ("This is pet match. I can help you find the perfect pet "
                  "for you. You can say, I want a dog.")
        reprompt = "What size and temperament are you looking for in a dog?"

        handler_input.response_builder.speak(speech).ask(reprompt)
        return handler_input.response_builder.response


class ExitIntentHandler(AbstractRequestHandler):
    """Single Handler for Cancel, Stop and Pause intents."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In ExitIntentHandler")
        handler_input.response_builder.speak("Bye").set_should_end_session(
            True)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for skill session end."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In SessionEndedRequestHandler")
        logger.info("Session ended with reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response

# Exception Handler classes
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch All Exception handler.

    This handler catches all kinds of exceptions and prints
    the stack trace on AWS Cloudwatch with the request envelope."""
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speech = "Sorry, I can't understand the command. Please say again."
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response


# Request and Response Loggers
class RequestLogger(AbstractRequestInterceptor):
    """Log the request envelope."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.info("Request Envelope: {}".format(
            handler_input.request_envelope))


class ResponseLogger(AbstractResponseInterceptor):
    """Log the response envelope."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.info("Response: {}".format(response))


# Data
required_slots = ["energy", "size", "temperament"]

slots_meta = {
    "pet": {
        "invalid_responses": [
            "I'm sorry, but I'm not qualified to match you with {}s.",
            "Ah yes, {}s are splendid creatures, but unfortunately owning one as a pet is outlawed.",
            "I'm sorry I can't match you with {}s."
        ]
    },
    "error_default": "I'm sorry I can't match you with {}s."
}

scentsee_api = {
    "base_url": "http://scentsee.com",
    "name": "/rest/collection/queryFull?query={}",
    "reco_by_id": "/rest/recommendation/byFavoriteFragranceId?ids[]={}",
}


# Utility functions
def get_resolved_value(request, slot_name):
    """Resolve the slot name from the request using resolutions."""
    # type: (IntentRequest, str) -> Union[str, None]
    try:
        return (request.intent.slots[slot_name].resolutions.
                resolutions_per_authority[0].values[0].value.name)
    except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
        logger.info("Couldn't resolve {} for request: {}".format(slot_name, request))
        logger.info(str(e))
        return None

def get_slot_values(filled_slots):
    """Return slot values with additional info."""
    # type: (Dict[str, Slot]) -> Dict[str, Any]
    slot_values = {}
    logger.info("Filled slots: {}".format(filled_slots))

    for key, slot_item in six.iteritems(filled_slots):
        name = slot_item.name
        try:
            status_code = slot_item.resolutions.resolutions_per_authority[0].status.code

            if status_code == StatusCode.ER_SUCCESS_MATCH:
                slot_values[name] = {
                    "synonym": slot_item.value,
                    "resolved": slot_item.resolutions.resolutions_per_authority[0].values[0].value.name,
                    "is_validated": True,
                }
            elif status_code == StatusCode.ER_SUCCESS_NO_MATCH:
                slot_values[name] = {
                    "synonym": slot_item.value,
                    "resolved": slot_item.value,
                    "is_validated": False,
                }
            else:
                pass
        except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
            logger.info("Couldn't resolve status_code for slot item: {}".format(slot_item))
            logger.info(e)
            slot_values[name] = {
                "synonym": slot_item.value,
                "resolved": slot_item.value,
                "is_validated": False,
            }
    return slot_values

def random_phrase(str_list):
    """Return random element from list."""
    # type: List[str] -> str
    return random.choice(str_list)

def get_brand(base_url, path, slot_values):
    """Return options for HTTP Get call."""
    url = base_url + path
    url = url.format(slot_values["perfume"]["resolved"])
    response = requests.get(url=url, params={})

    logger.info("Response: {}".format(response))

    brand = json.loads(response.text)
    brand = brand[0]["brand"]

    return brand

def get_recos_like_name(base_url, name_call, reco_call, slot_values):
    """Return options for HTTP Get call."""
    url = base_url + name_call

    query = ''
    if slot_values["perfume"]["resolved"] and slot_values["brand"]["resolved"]:
        query = slot_values["perfume"]["resolved"] + ' ' + slot_values["brand"]["resolved"]
    if slot_values["perfume"]["resolved"] and not slot_values["brand"]["resolved"]:
        query = slot_values["perfume"]["resolved"]

    url = url.format(query)

    logger.info("Requestig getId at: {}".format(url))

    response = requests.get(url=url, params={})

    logger.info("Response for getId: {}".format(response))

    response = json.loads(response.text)
    id = response[0]["id"]
    brand = response[0]["brand"]

    url = base_url + reco_call + '&maxResults=3'
    url = url.format(id)

    response = requests.get(url=url, params={})

    logger.info("Response for getReco: {}".format(response))

    def process(r):
        return r["name"] + ' by ' + r["brand"]

    recos = json.loads(response.text)
    recos = recos["recommendations"]
    recos = list(map(process, recos))

    logger.info("Recos: {}".format(str(recos)))

    if len(recos) > 2:
        recos = ', '.join(recos[:-1]) + ", or " + str(recos[-1])
    if len(recos) == 2:
        recos = ' and '.join(recos)
    if len(recos) == 1:
        recos = recos[0]

    recos = {
         "recos": recos,
         "brand": brand
    }

    logger.info("Passing recos: {}".format(recos["recos"]))

    return recos

def get_base_notes(base_url, name_call, reco_call, slot_values):
    """Return options for HTTP Get call."""
    url = base_url + name_call

    query = ''
    if slot_values["perfume"]["resolved"] and slot_values["brand"]["resolved"]:
        query = slot_values["perfume"]["resolved"] + ' ' + slot_values["brand"]["resolved"]
    if slot_values["perfume"]["resolved"] and not slot_values["brand"]["resolved"]:
        query = slot_values["perfume"]["resolved"]

    url = url.format(query)
    response = requests.get(url=url, params={})

    logger.info("Response for getId: {}".format(response))

    response = json.loads(response.text)
    id = response[0]["id"]
    brand = response[0]["brand"]

    url = base_url + reco_call
    url = url.format(id)

    logger.info("Requestig getId at: {}".format(url))

    response = requests.get(url=url, params={})

    logger.info("Response for getReco: {}".format(response))

    base_notes = json.loads(response.text)
    base_notes = base_notes["basedOn"][0]["dominantClasses"]

    base_notes = list(base_notes.items())

    max_strength = max(base_notes, key=itemgetter(1))[1]
    strongest_note = max(base_notes, key=itemgetter(1))[0]

    filter_set = set([max_strength])

    strongest = [bn for bn in base_notes if bn[1] in filter_set]
    strongest = [i[0] for i in strongest]
    if len(strongest) > 2:
        strongest = ', '.join(strongest[:-1]) + ", and " + str(strongest[-1])
    if len(strongest) == 2:
        strongest = ' and '.join(strongest)
    if len(strongest) == 1:
        strongest = strongest[0]

    rest = [bn for bn in base_notes if bn[1] not in filter_set]
    rest = [i[0] for i in rest]
    if len(rest) > 2:
        rest = ', '.join(rest[:-1]) + ", and " + str(rest[-1])
    if len(rest) == 2:
        rest = ' and '.join(rest)
    if len(rest) == 1:
        rest = rest[0]

    base_notes = {
        "strongest": strongest,
        "rest": rest,
        "brand": brand
    }

    return base_notes

def http_get(http_options):
    url = http_options["url"]
    params = http_options["path_params"]
    response = requests.get(url=url)

    if response.status_code < 200 or response.status_code >= 300:
        response.raise_for_status()

    return response.json()


# Skill Builder object
sb = SkillBuilder()

# Add all request handlers to the skill.
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HandleBaseNotesIntent())
sb.add_request_handler(HandleMakerIntent())
sb.add_request_handler(HandleRecommendLikeIntent())

# Add exception handler to the skill.
sb.add_exception_handler(CatchAllExceptionHandler())

# Add response interceptor to the skill.
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

# Expose the lambda handler to register in AWS Lambda.
lambda_handler = sb.lambda_handler()

a = {
				"perfume": {
					"name": "perfume",
					"value": "alien",
					"resolutions": {
						"resolutionsPerAuthority": [
							{
								"authority": "amzn1.er-authority.echo-sdk.amzn1.ask.skill.01d8540f-e5a8-4e77-948b-8729e433d568.perfumeType",
								"status": {
									"code": "ER_SUCCESS_MATCH"
								},
								"values": [
									{
										"value": {
											"name": "korrigan",
											"id": "9343e04c51509389c5f6488aace42ac2"
										}
									}
								]
							}
						]
					},
					"confirmationStatus": "NONE",
					"source": "USER"
				}
			}

if __name__ == "__main__":
    get_recos_like_name(
        base_url=scentsee_api["base_url"], name_call=scentsee_api["name"], reco_call=scentsee_api["reco_by_id"],
        slot_values=a)