import typer

from langroid.agent.chat_agent import ChatAgent, ChatAgentConfig
from langroid.agent.special.recipient_validator_agent import (
    RecipientValidator, RecipientValidatorConfig
)
from langroid.agent.task import Task
from langroid.language_models.openai_gpt import OpenAIChatModel, OpenAIGPTConfig
from langroid.utils.configuration import set_global, Settings
from langroid.utils.logging import setup_colored_logging


app = typer.Typer()

setup_colored_logging()


def chat() -> None:
    config = ChatAgentConfig(
        llm = OpenAIGPTConfig(
            chat_model=OpenAIChatModel.GPT4,
        ),
        vecdb = None,
    )
    router_agent = ChatAgent(config)
    router_task = Task(
        router_agent,
        name = "Router",
        system_message="""
        Your job is to send the current number to one of two people:
        If the number is even, send it to EvenHandler,
        and if it is odd, send it to OddHandler.
        The handlers will transform the number and give you a new number.        
        If you send it to the wrong person, you will receive a negative value.
        Your goal is to never get a negative number, so you must 
        clearly specify who you are sending the number to, by starting 
        your message with "TO[EvenHandler]:" or "TO[OddHandler]:".
        For example, you could say "TO[EvenHandler]: 4".
        """,
        llm_delegate=True,
        single_round=False,
    )
    even_agent = ChatAgent(config)
    even_task = Task(
        even_agent,
        name = "EvenHandler",
        system_message="""
        You will be given a number. 
        If it is even, divide by 2 and say the result, nothing else.
        If it is odd, say -10
        """,
        single_round=True,  # task done after 1 step() with valid response
    )

    odd_agent = ChatAgent(config)
    odd_task = Task(
        odd_agent,
        name = "OddHandler",
        system_message="""
        You will be given a number n. 
        If it is odd, return (n*3+1), say nothing else. 
        If it is even, say -10
        """,
        single_round=True,  # task done after 1 step() with valid response
    )
    validator_agent = RecipientValidator(
        RecipientValidatorConfig(
            recipients=["EvenHandler", "OddHandler"],
        )
    )
    validator_task = Task(validator_agent, single_round=True)

    router_task.add_sub_task([validator_task, even_task, odd_task])
    router_task.run("3")


@app.command()
def main(
        debug: bool = typer.Option(False, "--debug", "-d", help="debug mode"),
        no_stream: bool = typer.Option(False, "--nostream", "-ns", help="no streaming"),
        nocache: bool = typer.Option(False, "--nocache", "-nc", help="don't use cache"),
) -> None:
    set_global(
        Settings(
            debug=debug,
            cache=not nocache,
            stream=not no_stream,
        )
    )
    chat()


if __name__ == "__main__":
    app()
