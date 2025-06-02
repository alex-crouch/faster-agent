from pydantic import BaseModel
from typing import List

class SubTaskInfo(BaseModel):
    subTaskName: str
    goal: str
    inputs: List[str]
    outputs: List[str]
    challenges: List[str]
    fallback: bool

class PlanInfo(BaseModel):
    planName: str
    coreObjective: str
    assumptions: List[str]
    subtask: List[SubTaskInfo]

def main():
    # Create some example subtasks
    subtask1 = SubTaskInfo(
        subTaskName="FetchNewsStories",
        goal="Retrieve the latest news stories from the New York Times API",
        inputs=["API key", "Number of stories to retrieve"],
        outputs=["Raw news data", "Article timestamps"],
        challenges=["API rate limits", "Handling request failures"],
        fallback=True
    )
    
    subtask2 = SubTaskInfo(
        subTaskName="TransformToGossipStyle",
        goal="Rewrite news stories in Gossip Girl narrative style",
        inputs=["Raw news data", "Gossip Girl style guide"],
        outputs=["Transformed news stories"],
        challenges=["Maintaining factual accuracy", "Capturing authentic Gossip Girl tone"],
        fallback=False
    )
    
    # Create the main plan
    plan = PlanInfo(
        planName="NewsGossipTransformer",
        coreObjective="Transform NYT news into Gossip Girl style narratives",
        assumptions=["User has NYT API access", "3 stories is sufficient"],
        subtask=[subtask1, subtask2]
    )
    
    # DIFFERENT WAYS TO PRINT THE STRUCTURE
    
    # 1. Print the entire object (uses the __str__ representation)
    print("=== Printing the full object ===")
    print(plan)
    print()
    
    # 2. Access and print specific properties
    print("=== Accessing specific properties ===")
    print(f"Plan Name: {plan.planName}")
    print(f"Core Objective: {plan.coreObjective}")
    print(f"Assumptions: {', '.join(plan.assumptions)}")
    print()
    
    # 3. Iterate through subtasks
    print("=== Iterating through subtasks ===")
    for i, subtask in enumerate(plan.subtask, 1):
        print(f"\nSubtask {i}: {subtask.subTaskName}")
        print(f"  Goal: {subtask.goal}")
        print(f"  Inputs: {', '.join(subtask.inputs)}")
        print(f"  Outputs: {', '.join(subtask.outputs)}")
        print(f"  Challenges: {', '.join(subtask.challenges)}")
        print(f"  Fallback required: {subtask.fallback}")
    print()
    
    # 4. Convert to dictionary
    print("=== Converting to dictionary ===")
    plan_dict = plan.model_dump()
    print(plan_dict)
    print()
    
    # 5. Convert to JSON string with pretty formatting
    print("=== Converting to JSON string ===")
    import json
    # Using the built-in json method from pydantic
    plan_json = plan.model_dump_json(indent=2)
    print(plan_json)
    print()
    
    # 6. Converting back from JSON
    print("=== Converting JSON back to object ===")
    new_plan = PlanInfo.model_validate_json(plan_json)
    print(f"Recovered plan name: {new_plan.planName}")
    print(f"Number of subtasks: {len(new_plan.subtask)}")

if __name__ == "__main__":
    main()