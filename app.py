import os
import re
import streamlit as st
import google.generativeai as genai

# Load environment variables

# Define action regex pattern
action_re = re.compile(r'^Action: (\w+): (.*)$')

# Define functions for actions using the Gemini API
def generate_treatment(diabetes_type):
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Suggest a medical treatment plan for a {diabetes_type} diabetes patient.")
    return response.text

def suggest_meal(preference):
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Suggest a meal plan for a {preference} diabetic diet.")
    return response.text

def exercise_plan(level):
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Generate an exercise plan for a {level} diabetes patient.")
    return response.text

def motivational_quote():
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content("Give a motivational quote for a diabetes patient.")
    return response.text

# Mapping actions to functions
known_actions = {
    "generate_treatment": generate_treatment,
    "suggest_meal": suggest_meal,
    "exercise_plan": exercise_plan,
    "motivational_quote": motivational_quote
}

# Chatbot class to handle conversation
class Chatbot:
    def __init__(self, system=""):
        self.system = system
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system})
    
    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result
    
    def execute(self):
        prompt = "\n".join([f'{msg["role"]}: {msg["content"]}' for msg in self.messages])
        model = genai.GenerativeModel('gemini-1.5-flash')
        raw_response = model.generate_content(prompt)
        return raw_response.text

# Query function
def query(question, max_turns=5):
    bot = Chatbot(prompt)
    next_prompt = question
    i = 0
    query_result = ""
    while i < max_turns:
        i += 1
        result = bot(next_prompt)
        query_result += result + "\n\n"
        actions = [action_re.match(a) for a in result.split('\n') if action_re.match(a)]
        if actions:
            # There is an action to run
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception(f"Unknown action: {action}: {action_input}")
            observation = known_actions[action](action_input)
            query_result += f"Observation: {observation}\n\n"
            next_prompt = f"Observation: {observation}"
        else:
            break
    return query_result

# Prompt for the chatbot
prompt = """
You are a medical assistant specialized in helping patients with all types of diabetes. You provide treatment advice, meal suggestions, exercise plans, and motivational support. You are knowledgeable about the following types of diabetes:

1. Type 1 Diabetes: Autoimmune disorder where the body attacks insulin-producing cells.
2. Type 2 Diabetes: Often related to lifestyle, where the body becomes insulin resistant.
3. Gestational Diabetes: Occurs during pregnancy and usually resolves post-delivery.
4. LADA (Latent Autoimmune Diabetes in Adults): Similar to Type 1 but slower in progression.
5. MODY (Maturity-Onset Diabetes of the Young): A rare genetic form of diabetes.
6. Pre-diabetes: Early stage where blood sugar levels are elevated but not yet Type 2.
7. Secondary Diabetes: Caused by other medical conditions or medications.

Your available actions are:
generate_treatment:
e.g. generate_treatment: Type 1
Generates a treatment plan based on the patient's type of diabetes.
suggest_meal:
e.g. suggest_meal: Low-sugar
Suggests a meal plan for diabetic patients based on dietary preferences.
exercise_plan:
e.g. exercise_plan: Beginner
Generates an exercise plan tailored to diabetic patients' fitness levels.
motivational_quote:
e.g. motivational_quote:
Returns a motivational quote for diabetes patients.
Example session:
Question: Can you help me with a treatment plan for a Type 2 diabetes patient?
Thought: I should generate a treatment plan.
Action: generate_treatment: Type 2
Observation: Here is a Type 2 diabetes treatment plan: Metformin, lifestyle modifications, and regular blood sugar monitoring.
Answer: I suggest starting with Metformin, lifestyle modifications, and regular blood sugar monitoring.
"""

# Streamlit UI
st.sidebar.title("Settings")

# Input for Google API Key in the sidebar
google_api_key = st.sidebar.text_input("Enter your Google API Key:", type="password")

# Store the API key in the environment variable if provided
if google_api_key:
    os.environ['GOOGLE_API_KEY'] = google_api_key
    genai.configure(api_key=google_api_key)  # Reconfigure the API with the new key

# Main app title
st.title("Diabetes Management Assistant")

# Multiple select box for diabetes type
diabetes_type = st.multiselect(
    "Select your diabetes type:",
    options=["Type 1", "Type 2", "Gestational", "LADA", "MODY", "Pre-diabetes", "Secondary Diabetes"],
    default=["Type 2"]
)

# Multiple select box for dietary preferences
dietary_preferences = st.multiselect(
    "Select dietary preferences:",
    options=["Low-sugar", "Low-carb", "High-protein", "Vegan", "Keto", "Mediterranean", "Gluten-free", "Paleo"],
    default=["Low-sugar"]
)

# Multiple select box for exercise level
exercise_levels = st.multiselect(
    "Select your fitness level(s) for exercise plan:",
    options=["Beginner", "Intermediate", "Advanced"],
    default=["Beginner"]
)

# Optional user input
user_input = st.text_input("Optional: Enter additional question or clarification:")

if st.button("Generate Response"):
    # If user input is empty, auto-generate based on selected options
    if not user_input:
        if diabetes_type:
            question = f"Can you help me with a {', '.join(diabetes_type)} diabetes treatment plan?"
        else:
            st.error("Please select at least one diabetes type.")

        if dietary_preferences:
            question += f" Suggest a meal plan for a {', '.join(dietary_preferences)} diabetic diet."

        if exercise_levels:
            question += f" Generate an exercise plan for a {', '.join(exercise_levels)} fitness level."

        response = query(question)
    else:
        # If user input is provided, append it to the selected options
        response = query(user_input)
    
    # Display the response
    st.markdown("### Response:")
    st.markdown(response)
