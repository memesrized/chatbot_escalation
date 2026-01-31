# Open questions and assumptions

## Product/business open questions and requirements:
1. Proper list of escalation reasons defined and approved by product team.
2. Defined business metrics / preferences and decision thresholds to optimize the trade-off between user satisfaction and cost.
    - i.e. define error costs for:
        - escalated when not needed
        - escalated too early
        - escalated too late
        - not escalated when needed
3. UX requirements (e.g. streaming vs non-streaming answer generation) for real-time performance and latency.
4. Level of explainability and business rules following reuired by classifier.
5. Plans for future extensibility (e.g. adding new models, changing architecture) to ensure maintainability.

### Product assumptions made:
1. Escalation reasons list is fixed for the initial version.
    - Compiled based on given dataset reasons generalization.
2. Balance between false positives and false negatives is not yet defined.
    - It's required to have flexibility for future tuning and adjustments.
    - Initial focus is on maximizing user satisfaction, even at the expense of budget and with tolerance for some false positives.
    - User satisfaction - minimizing cases of "not escalated when needed" and "escalated too late" is the top priority.
3. Reasonable real-time performance is required, but precision is the main focus and streaming is not mandatory.
    - Assume, the non-streaming bot response is common across the industry at the moment.
    - It's close to human agent interaction and response time anyway.
    - If streaming is required, it can be added later as an improvement.
4. Detailed explanation of decision is definitely required in the future.
    - Now it's enough to have structured output with reason codes.
5. The system should be designed with modularity and extensibility in mind.
    - Allow easy swapping of models, changing architecture, and adding new features in the future.
    - Extensible decision logic and state tracking.
        - E.g. adding new counters or metrics:
            - sentiment analysis (e.g. frustration level)
            - unsolved issues tracking
            - tracking of failed models attempts
        - So later we can experiment with different decision strategies without major code changes.
            - e.g. rules-based by sentiment + unresolved issues
            - ML-based classifier on top of tracked metrics


## Technical open questions and requirements:
1. Expected scale and concurrency requirements to ensure system scalability.
2. Expected latency requirements for real-time interactions.
3. Available inference providers / infrastructure for hosting models.
4. Data availability for evaluation and fine-tuning.

### Technical assumptions made:
1. Initial scale is low-medium, so scalability is not a primary concern.
    - The system should be designed to allow future scalability improvements if needed.
    - Small state is tracked in code, no external storage required for now, but should not be a problem to store it in db with conversation id later.
2. Latency should be minimized, and real-time streaming is not mandatory.
    - ~1-2? sec delay before chatbot processing starts is ~ok
    - Streaming would allow optimizations, but it's not a must-have for the initial version.
3. Flexibility is needed for the sake of experimentation and evaluation of **this** solution as take-home project.
    - Any LangChain-supported model provider can be used.
    - Prefer low-latency providers like Groq with gpt-oss for cost-effective inference.
4. Data is limited, but representative enough for initial evaluation and fine-tuning.
    - Even though it lacks cases with turn-by-turn labels, it can be used for overall evaluation.
        - but missing early/late escalation measurement

# Current decisions and future improvements

## Decisions made / Design choices:
- Prompt with explanation vs shots
    - prompt with instructions (chosen option)
        - pros:
            - more flexible for future changes
            - easier to maintain and update
        - cons:
            - requires solid approved list of reasons from product team
            - may require more prompt engineering to achieve desired performance
    - few-shots
        - pros:
            - may provide better context for the model
            - can demonstrate desired output format more clearly
        - cons:
            - less flexible for future changes
            - harder to maintain and update
            - may bias the model towards specific examples
    - Why prompt with instructions was chosen:
        - flexibilty is really important for initial version
        - I don't know if the data is representative enough to cover all edge cases in few-shots
- Run classification after each turn vs only after chatbot turn
    - each turn (chosen option)
        - pros:
            - allows for quicker escalation if user is upset or angry
            - prevents waiting for chatbot response in critical situations
            - allows for more responsive handling of user emotions
        - cons:
            - doubles the number of requests (cost and latency)
    - only after chatbot turn
        - pros:
            - reduces the number of requests (cost and latency)
        - cons:
            - may delay escalation in critical situations
            - less responsive to user emotions
    - Why each turn was chosen:
        - customer satisfaction is top priority
        - even if it increases cost and latency, it's worth it to ensure timely escalation
        - It's impelemented in a way that allows easy switching later if needed
            - you can turn off the "user turn" by replacing user this classifier with dummy that always returns no escalation (there are two, one for user and one for bot turns)
- sync vs async calls
    - sync (chosen option)
        - pros:
            - simpler implementation
            - easier to debug and maintain
        - cons:
            - may increase overall latency
    - async
        - pros:
            - can reduce overall latency by parallelizing requests
        - cons:
            - more complex implementation
            - harder to debug and maintain
    - Why sync was chosen:
        - simplicity is key for initial version
        - async can be added later as an improvement if needed
- streaming vs non-streaming
    - non-streaming (chosen option)
        - pros:
            - simpler implementation
            - easier to debug and maintain
        - cons:
            - may increase perceived latency for users
    - streaming
        - pros:
            - can improve perceived latency for users
        - cons:
            - more complex implementation
            - harder to debug and maintain
    - Why non-streaming was chosen:
        - simplicity is key for initial version
        - streaming can be added later as an improvement if needed
        - also, many chatbots still use non-streaming responses, so it's acceptable for initial version
- model choice
    - gpt-oss via groq (chosen option)
        - pros:
            - cost-effective
            - low-latency inference provider
            - good performance for classification tasks
        - cons:
            - may not be as powerful as some proprietary models
    - why gpt-oss via groq was chosen:
        - balances cost and performance effectively
        - fast and smart enough for the task at hand
        - easy to switch to other models later if needed via langchain config
- one time classification vs voting
    - one time classification (chosen option)
        - pros:
            - simpler implementation
            - lower cost and latency
        - cons:
            - may be less robust to model errors
            - I already noticed some instability in outputs during testing
                - scores jumping around a bit (from ~90% to 75%), but usually ~85%
    - voting
        - pros:
            - can improve robustness by aggregating multiple predictions
        - cons:
            - more complex implementation
            - higher cost and latency
    - Why one time classification was chosen:
        - simplicity is key for initial version
        - voting can be added later as an improvement if needed

## Future improvements (if time permits):
- switch to async calls for more production ready system
- switch to streaming
    - easy enough and allows us to make some optimizations
        - e.g. call classification after the user message in parallel with chatbot generation
        - and if classification says "escalate", we can stop chatbot generation right away
- data augmentation for better evaluation
    - turn-by-turn labels, to keep track of early/late escalation
    - good to have also cases when escalation was needed, but not done
- better prompt engineering
- more advanced state tracking
    - e.g. sentiment analysis
- more advanced decision logic
    - make proper rules based on tracked metrics like frustration, unresolved issues, failed attempts
    - now unresolved and failed_attempt are passed to the model as context only
    - and frustration is just to eval the model in the background
- prompt caching to reduce cost and latency
    - need to research if structured output is cached by model providers
    - if not, we can try to put as much as we can in the prompt itself
- better --help for the CLI itself
- latency evaluation for different models, providers, and configurations
    - to make better trade-offs between cost, performance, and user experience
    - now it's <1 sec for gpt-oss via groq, which is good enough
- add voting ensemble for more robust predictions
    - e.g. majority voting over multiple model outputs
    - or weighted voting based on model confidence
    - it's pricier, but will definitely improve robustness
- add set code linters / formatters / pre-commit hooks
    - to ensure code quality and consistency
- test alternative conversation formats to reduce token count
    - current: indented JSON (high tokens, good performance)
    - candidates: YAML (only as alternative to indented JSON), compact JSON (should be really good, but doesn't work well for some reason), custom format
    - need to benchmark impact on both cost and model accuracy
- investigate prompt caching behavior with Pydantic schemas
    - test if field descriptions in structured output schemas are cached
    - determine optimal placement of instructions (schema vs prompt template)
    - may need to move some descriptions to prompt for better caching
