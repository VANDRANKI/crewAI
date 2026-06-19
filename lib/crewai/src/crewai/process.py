from enum import Enum


class Process(str, Enum):
    """Execution strategy for how a :class:`~crewai.Crew` runs its tasks.

    Choose a process when constructing a :class:`~crewai.Crew` to control the
    order in which agents pick up and complete tasks.

    Attributes:
        sequential: Tasks are executed one after another in the order they are
            defined.  Each task receives the output of the previous task as
            context.  This is the simplest and most predictable strategy.
        hierarchical: A manager agent dynamically allocates tasks to worker
            agents based on their capabilities.  The manager decides execution
            order at runtime, which can improve parallelism and adaptability
            for complex workflows.

    Example:
        .. code-block:: python

            from crewai import Crew, Process

            crew = Crew(
                agents=[researcher, writer],
                tasks=[research_task, write_task],
                process=Process.sequential,
            )
    """

    sequential = "sequential"
    hierarchical = "hierarchical"
    # TODO: consensual = 'consensual'
