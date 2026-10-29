from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
from app.config import settings

TYPESAFE_API_KEY =settings.TYPESAFE_API_KEY

def callSimpleSystemOneJev(idAnswer:str,type:str,state:str,instructions:str,criteria:dict)-> dict:
    """
    Llama a la API de TypeSafe para procesar un estado y obtener una respuesta generada por el modelo de lenguaje.
    Args:
        TYPESAFE_API_KEY (str): La clave de API para autenticación.
        idAnswer (str): El identificador de la respuesta.
        type (str): El tipo de pregunta (Choice, Score, Noul).
        state (str): El estado o mensaje a procesar.
        instructions (str): Instrucciones para el modelo.
        criteria (dict): Criterios para la evaluación.
    Returns:
        dict: La respuesta generada por el modelo de lenguaje.
    """
    try:
        print(f"Enter callSystemOneJev with state: {state}, idAnswer: {idAnswer}, type: {type}, instructions: {instructions}, criteria: {criteria}")
        TYPESAFE_API_KEY = settings.TYPESAFE_API_KEY
        client = TypeSafeClient(
            api_key=TYPESAFE_API_KEY
        )
        match type:
            case "Choice":
                content = Choice(instructions=instructions, criteria=criteria)
            case "Score":
                content = Score(instructions=instructions, criteria=criteria)
            case "Noul":
                content = Noul(instructions=instructions)
            case _:
                raise ValueError(f"Invalid question type: {type}")
        print(f"TypeSafeClient created, calling system_one with content: {content}")
        response = client.system_one(
            state=state,
            questions={
                idAnswer: content
            },
        )
        print(f"Received response from TypeSafe API: {response}")
        # SystemOneResponse es un modelo Pydantic; se convierte a dict para poder enviarlo por WebSocket
        return response.model_dump(mode="json")
    except Exception as e:
        return {
            "error": str(e),
            "response": {}
        }

# How to use the function:
# Choice
# {
#   "state": "My running shoes arrived in the wrong size. Can I swap them for a size 10?",
#   "questions": {
#     "department": {
#       "type": "choice",
#       "instructions": "Which team should handle this?",
#       "criteria": {
#         "returns": "Exchanges, wrong or damaged items",
#         "shipping": "Delivery status, delays, lost packages",
#         "billing": "Charges, invoices, payment problems"
#       }
#     }
#   }
# }
# Score
# {
#   "state": "The export button crashes the settings page in Safari. It works in Chrome, but a few of our customers only use Safari.",
#   "questions": {
#     "bug_severity": {
#       "type": "score",
#       "instructions": "How severe is the reported issue?",
#       "criteria": [
#         "Cosmetic; no impact to functionality",
#         "Broken or degraded feature, but workaround exists",
#         "Blocking issue; no workaround exists"
#       ]
#     }
#   }
# }

# Noul
# {
#   "state": "I have asked three times now. Can I please just talk to a real person?",
#   "questions": {
#     "is_human_escalation": {
#       "type": "noul",
#       "instructions": "Is the customer asking for a human agent?"
#     },
#     "is_repeat_contact": {
#       "type": "noul",
#       "instructions": "Has the customer contacted support about this before?",
#       "criteria": {
#         "true": "Mentions a prior attempt, ticket, or that they have asked before",
#         "false": "No sign of any previous contact"
#       }
#     }
#   }
# }
# test1 = callSystemOneJev("department","Choice",ticket,"Which team should handle this",criteria)
# print(test1)

        