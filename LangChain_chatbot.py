import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

import re

# Load environment variables and set up OpenAI API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Define general prompt to set the internal context for the interview
general_prompt = """
You are an anthropologist conducting a semi-structured interview about memorable wine experiences.
Your goals are:
- Encourage participants to reflect on and describe their last memorable wine experience in detail.
- Cover topics including sensory perceptions, environment, emotional impact, and their familiarity with wine.
- Ask one question at a time, based on their previous response, and prompt them to go deeper into aspects that emerge naturally in conversation.
- Ensure the conversation flows smoothly, with logical transitions based on the participant's answers.
- Do not make up any answers or simulate the participant's responses.
- Do not include any additional text beyond the next question to ask.
- Do not ask redundant questions or rephrase previous questions.
- Introduce new subtopics not yet covered.
When all topics have been covered and the participant has fully expressed themselves, end the conversation nicely, thanking them for taking the time to share their memory.
At the end, ask the participant about their level of experience with wine, any training they may have, how often they drink wine, and on what occasions.
"""

# Initialize the language model
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    api_key=api_key,
    temperature=0.7,
    max_tokens=200  # Adjust as needed
)

# Connect to SQLite database
conn = sqlite3.connect('interview_data.db')
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS interview_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        response TEXT,
        timestamp TEXT
    )
''')
conn.commit()

# Define a logging function for storing the grammar-corrected answer
def log_response(question, response):
    timestamp = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO interview_logs (question, response, timestamp)
        VALUES (?, ?, ?)
    ''', (question, response, timestamp))
    conn.commit()

# Define grammar correction function to correct participant answers
def grammar_check(input_text):
    if not input_text.strip():
        # Return an empty string if there's nothing to correct
        return ''
    prompt = f"""
    Please correct any spelling and grammar mistakes in the following text without changing its meaning.
    Only provide the corrected text without any additional comments or explanations.

    Text: {input_text}
    """
    messages = [
        SystemMessage(content="You are a helpful assistant that corrects grammar and spelling."),
        HumanMessage(content=prompt)
    ]
    corrected_response = llm.invoke(messages)
    # Extract only the corrected text
    corrected_text = corrected_response.content.strip()
    return corrected_text

# Main topics with their initial questions
question_topics = {
    "sensory": "What aromas, flavors, or textures were notable in that wine?",
    "environment": "Where did this experience take place, and who were you with?",
    "emotion": "Reflecting on this memory, how does it make you feel now?"
}

# Subtopics under each main topic
subtopics = {
    "sensory": ["aromas", "flavors", "sight", "colors", "textures", "temperature", "tannins", "sounds"],
    "environment": ["location", "occasion", "time of day", "people with you", "atmosphere", "music", "description of the surroundings", "landscape"],
    "emotion": ["emotions now", "emotions during the event", "pleasure associated", "surprise", "unexpected part", "anything out of the ordinary"]
}

# Final question about participant's wine experience level
experience_question = "To conclude, could you tell me about your level of experience with wine? Do you have any training, how often do you drink wine, and on what occasions?"

# Function to analyze the participant's response for covered topics
def analyze_response_for_topics(response, remaining_topics):
    prompt = f"""
Based on the following response, identify which, if any, of the following topics have been addressed: {', '.join(remaining_topics)}.
Response: '{response}'
List the topics that have been covered, or write 'none' if none have been covered.
"""
    messages = [
        SystemMessage(content=general_prompt),
        HumanMessage(content=prompt)
    ]
    analysis = llm.invoke(messages)
    if 'none' in analysis.content.lower():
        covered_topics = []
    else:
        covered_topics = [topic.strip().lower() for topic in analysis.content.split(',')]
    return covered_topics

# Function to analyze the participant's response for covered subtopics
def analyze_response_for_subtopics(response, main_topic, remaining_subtopics):
    prompt = f"""
Based on the following response, identify which, if any, of the following subtopics related to '{main_topic}' have been addressed: {', '.join(remaining_subtopics)}.
Response: '{response}'
List the subtopics that have been covered, or write 'none' if none have been covered.
"""
    messages = [
        SystemMessage(content=general_prompt),
        HumanMessage(content=prompt)
    ]
    analysis = llm.invoke(messages)
    if 'none' in analysis.content.lower():
        covered_subtopics = []
    else:
        covered_subtopics = [topic.strip().lower() for topic in analysis.content.split(',')]
    return covered_subtopics

# Function to get recent conversation history
def get_recent_conversation(conversation_history, num_exchanges=2):
    exchanges = conversation_history.strip().split('\n')
    recent_exchanges = exchanges[-(num_exchanges*2):]  # Each exchange consists of an interviewer and participant line
    return '\n'.join(recent_exchanges)

# Function to generate the next question based on the participant's last response
def generate_next_question(conversation_history, last_response, next_topic, remaining_subtopics):
    recent_history = get_recent_conversation(conversation_history)
    prompt = f"""
As an anthropologist conducting an interview about memorable wine experiences, generate only the next question to ask the participant.
Focus on introducing the main topic '{next_topic}'.
The question should encourage the participant to share details about this new topic.
Do not make up any answers or simulate the participant's responses. Do not include any additional text.
Do not ask redundant questions or rephrase previous questions.
Use the following recent conversation history for context:
{recent_history}
Participant's last response: '{last_response}'
Subtopics under '{next_topic}' to be covered: {', '.join(remaining_subtopics)}
"""
    messages = [
        SystemMessage(content=general_prompt),
        HumanMessage(content=prompt)
    ]
    next_question = llm.invoke(messages)
    return next_question.content.strip()

# Function to generate a subtopic question
def generate_subtopic_question(conversation_history, last_response, main_topic, subtopic, remaining_subtopics):
    recent_history = get_recent_conversation(conversation_history)
    prompt = f"""
As an anthropologist conducting an interview about memorable wine experiences, generate only the next question to ask the participant.
Focus on introducing the subtopic '{subtopic}' under the main topic '{main_topic}'.
The question should encourage the participant to share details about this new subtopic.
Do not make up any answers or simulate the participant's responses. Do not include any additional text.
Do not ask redundant questions or rephrase previous questions.
Use the following recent conversation history for context:
{recent_history}
Participant's last response: '{last_response}'
Subtopics already covered under '{main_topic}': {', '.join(asked_subtopics[main_topic])}
Remaining subtopics under '{main_topic}': {', '.join(remaining_subtopics)}
"""
    messages = [
        SystemMessage(content=general_prompt),
        HumanMessage(content=prompt)
    ]
    subtopic_question = llm.invoke(messages)
    return subtopic_question.content.strip()

# Conduct the interview function
def conduct_interview():
    asked_questions = set()
    global asked_subtopics
    asked_subtopics = {}
    last_response = ""
    conversation_history = ""

    # Start with the initial question
    initial_question = "Tell me about the last memorable wine experience you've had."
    question = initial_question
    print(question)
    while True:
        response = input()
        corrected_response = grammar_check(response)
        if not corrected_response.strip():
            print("I'm sorry, I didn't catch that. Could you please share your experience?")
            continue  # Prompt the participant again
        break  # Exit the loop if a valid response is received

    # Log and process the response
    log_response(question, corrected_response)
    print(f"Response (Corrected): {corrected_response}\n")
    last_response = corrected_response
    conversation_history += f"Interviewer: {question}\nParticipant: {corrected_response}\n"

    # Analyze response for main topics covered
    remaining_topics = list(question_topics.keys())
    covered_topics = analyze_response_for_topics(last_response, remaining_topics)
    for topic in covered_topics:
        if topic in question_topics:
            asked_questions.add(topic)

    # Now, process each main topic
    for main_topic in question_topics:
        # Initialize subtopics for this main topic
        asked_subtopics[main_topic] = set()

        # Determine remaining subtopics
        remaining_subtopics = [st for st in subtopics[main_topic] if st not in asked_subtopics[main_topic]]

        if main_topic not in asked_questions:
            # Generate a personalized question to introduce the main topic
            next_question = generate_next_question(conversation_history, last_response, main_topic, remaining_subtopics)
            question = next_question
            print(question)
            while True:
                response = input()
                corrected_response = grammar_check(response)
                if not corrected_response.strip():
                    print("I'm sorry, could you please provide more details?")
                    continue  # Prompt the participant again
                break  # Exit the loop if a valid response is received
            log_response(question, corrected_response)
            print(f"Response (Corrected): {corrected_response}\n")
            last_response = corrected_response
            conversation_history += f"Interviewer: {question}\nParticipant: {corrected_response}\n"
            asked_questions.add(main_topic)
            # Analyze response for subtopics covered
            covered_subtopics = analyze_response_for_subtopics(last_response, main_topic, remaining_subtopics)
            for st in covered_subtopics:
                if st in subtopics[main_topic]:
                    asked_subtopics[main_topic].add(st)
        else:
            # Analyze last response for subtopics covered
            covered_subtopics = analyze_response_for_subtopics(last_response, main_topic, remaining_subtopics)
            for st in covered_subtopics:
                if st in subtopics[main_topic]:
                    asked_subtopics[main_topic].add(st)

        # Ask at least 2 subtopic questions
        subtopic_questions_asked = 0
        while subtopic_questions_asked < 2:
            remaining_subtopics = [st for st in subtopics[main_topic] if st not in asked_subtopics[main_topic]]
            if not remaining_subtopics:
                break  # No more subtopics to ask about
            # Select a subtopic not yet covered
            subtopic = remaining_subtopics[0]
            # Generate a personalized follow-up question
            subtopic_question = generate_subtopic_question(conversation_history, last_response, main_topic, subtopic, remaining_subtopics)
            question = subtopic_question
            print(question)
            while True:
                response = input()
                corrected_response = grammar_check(response)
                if not corrected_response.strip():
                    print("I'm sorry, could you please provide more details?")
                    continue  # Prompt the participant again
                break  # Exit the loop if a valid response is received
            log_response(question, corrected_response)
            print(f"Response (Corrected): {corrected_response}\n")
            last_response = corrected_response
            conversation_history += f"Interviewer: {question}\nParticipant: {corrected_response}\n"
            # Update asked_subtopics
            asked_subtopics[main_topic].add(subtopic)
            subtopic_questions_asked += 1
            # Analyze response for subtopics covered
            covered_subtopics = analyze_response_for_subtopics(last_response, main_topic, remaining_subtopics)
            for st in covered_subtopics:
                if st in subtopics[main_topic]:
                    asked_subtopics[main_topic].add(st)

    # Conclude with the participant's experience level
    question = experience_question
    print(question)
    while True:
        response = input()
        corrected_response = grammar_check(response)
        if not corrected_response.strip():
            print("I'm sorry, could you please provide more details?")
            continue  # Prompt the participant again
        break  # Exit the loop if a valid response is received
    log_response(question, corrected_response)
    print(f"Response (Corrected): {corrected_response}\n")
    conversation_history += f"Interviewer: {question}\nParticipant: {corrected_response}\n"

    # End the interview with a thank-you message
    print("Thank you for sharing your experiences and memories. It’s been a pleasure to learn about your memorable wine experience.")

# Run the interview
conduct_interview()

# Close the database connection when done
conn.close()
