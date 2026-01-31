# Senior Machine Learning Engineer Assignment

## Time budget
We recommend spending around 8 hours on this task. You may invest more time if you wish, but your submission will be evaluated as if completed within one standard working day.

## Submission guideline
Upload your solution to the provided link.

## Background
SumUp’s Operations team manages a customer support (CS) chatbot that handles a high volume of inquiries from merchants in various countries. While the chatbot resolves many issues independently, there are situations where escalation to a human agent is necessary to ensure efficient and satisfactory support. For instance, if the bot cannot resolve a problem or if a user shows signs of frustration. Escalation should happen at the right time, too early wastes agent time, too late risks customer frustration.

You are given a small corpus of multi-turn chat transcripts annotated with `is_escalation_needed` labels and the reasons why such escalations are granted. Each conversation consists of user and bot messages. Labels indicate whether an escalation is warranted at that turn.

Your task is to design and prototype a system that predicts when to escalate during an ongoing conversation.

## Task
Design and prototype an ML/AI system that detects when escalation to a human agent is needed during a conversation. Design your approach so it would work in production in terms of logic, data flow, and interfaces. We do not evaluate deployment, infra, monitoring, or other production-ops topics.

During your solution, make sure to consider both potential product and technical requirements. Identify and discuss the main technical challenges you anticipate.

Apply good engineering practices throughout. Write clean, maintainable code with a strong focus on readability. You may use AI tools to assist you in creating your solution, but ensure you fully understand the output and feel confident presenting and explaining each line of the code.

If your solution relies on AI services (e.g., LLMs), we recommend choosing a model that offers a free-tier quota (such as Google Gemini).

Include a simple command-line interface (CLI) that allows simulating a conversation and testing the escalation logic.

## Documentation
Document your design choices and why you chose this approach. Include your assumptions, open questions, and challenges which you foresee when bringing your prototype to production. Describe what you would have done differently if you had more time and resources available.

You may include diagrams or flowcharts to illustrate your architecture or decision process. Treat the documentation as important as your code.

## Evaluation criteria
We understand your time is limited and will evaluate accordingly. Please focus on the core task. We do not assess the chatbot’s detailed responses to user queries; our evaluation focuses solely on its escalation behavior.

Our evaluation of your solution will focus on:
- **Solution relevancy:** How well does your approach meet the requirements? Is it adaptable to future changes (e.g., evolving escalation policies, technical requirements, …)?
- **Quality of code:** Is your code readable and maintainable?
- **Documentation:** Is your reasoning clear, complete, and easy to follow?

## Deliverables
Submit your code with a short README explaining how to run it, and a separate documentation file as described above.

## Data
You will receive a labeled dataset. An example schema is shown below.

### JSON Example
```json
{
  "conversation_id": "c001",
  "conversation_history": [
    {"role": "bot", "message": "Hi, how can I help you?"},
    {"role": "user", "message": "where is my money?"},
    {"role": "bot", "message": "Could you please give me more information about the issue of your money?"},
    {"role": "user", "message": "I already explained many times to you! I tried to contact support but no one answered. I need an agent now"}
  ],
  "is_escalation_needed": true,
  "reasoning": "The user has explained that they tried to contact Customer Support many times without success. They are frustrated and requesting agent support. Therefore, escalation is needed in this case."
}
```

**Full dataset.**
