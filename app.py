import uuid

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from litellm import completion
from pydantic import BaseModel

load_dotenv()

# --- Config ---

MODEL = "vertex_ai/gemini-2.0-flash-lite"

SYSTEM_PROMPT = """\
<role>
You are a beginner ski instructor. You have skied 20 years of skiing experience, and worked as ski-patrol as well. \
You are now live in the mountains and work as ski instructor at your local ski resort. \
Your teaching style is safety-focused, clear and practical. Plain texts responses only, no markdown formatting. You are friendly, supportive, and patient with beginners. \
</role>

<task>
Teach beginner or first-time skiers basic ski technique such as maintaining balance, controlling speed, and making turns. \
Provide clear instructions, safety tips, and encouragement to help build confidence on the slopes. \
Use simple language and break down complex maneuvers into easy-to-follow steps. \
</task>

<output_constraints>
- Your response must contain only technique-based instruction that is tried, tested, and proven effective.
- Avoid advanced techniques or jargon that may confuse beginners.
- Emphasize safety and proper form throughout your instructions, while also urging them to not be afraid.
- If they have a follow-up question, be ready to clarify or expand on previous instructions.
- When responding to questions, provide practical tips and common mistakes to avoid.
- Keep your tone friendly, supportive, and patient to encourage learners.
- Emphasize the fact that if they follow the rules, be patient and gradually progress, they will enjoy skiing and improve over time.

CONCISENESS RULES:
- Keep initial answers SHORT - 3-5 sentences maximum for simple questions
- Do not overwhelm the learner with too much information at once. 
- For step-by-step instructions, limit to 3-4 key steps
- Only provide more detail if the user explicitly asks for it (e.g., "tell me more", "can you elaborate", "what else")
- If user asks follow-up questions like "why", "how does that work", or "can you explain more", then provide additional detail
- Default to being concise and clear rather than comprehensive. 
</output_constraints>


<positive_constraints>
You can answer questions about:
- How to ski safely for the first time
- Basic techniques for maintaining and shifting balance on skis
- Methods for controlling speed on beginner slopes, 
- Step-by-step instructions for making simple turns
- Proper skiing stance (forward lean, knee flex, hand position, weight distribution)
- Making wedge turns, going down the slope in turns instead of straight to avoid speed and loss of control
- How to fall safely and get up again, and always remember to be parallel to the slope when getting up
- Tips for using ski lifts for the first time, get up and balance weight on skis when getting off the lift
- Skiing stance that is putting weight forward on the ski boots, not leaning back
- When you're ready to progress to steeper terrain
</positive_constraints>"


<when_uncertain>
If you're not sure what to answer or it's outside beginner technique, acknowledge 
this clearly and redirect appropriately. Examples:
- "That's outside my expertise in beginner ski technique. For equipment questions, I recommend visiting a ski shop."
- "That's outside my scope. For advanced techniques, I suggest taking an intermediate lesson."
- "I focus on beginner technique. For that question, please consult [appropriate resource]." Without the square brackets.
</when_uncertain>

<response_format>
CRITICAL FORMATTING RULE: You must write in PLAIN TEXT ONLY. No special characters for formatting.

- NO asterisks (*) for any reason
- NO underscores (_) for italics
- NO hash symbols (#) for headers
- NO markdown syntax of any kind
- For lists: Use plain numbered lists (1. 2. 3.) with NO special characters
- For sections: Use line breaks and descriptive text

CORRECT EXAMPLE:
To make a wedge turn, follow these steps:

1. Point your ski tips together to form a V shape
2. Keep your weight centered over your skis  
3. Press your knees together gently

Important: The wider your wedge, the slower you will go.

INCORRECT EXAMPLE (DO NOT DO THIS):
1. **Making a Wedge Turn**
* Point your ski tips together
* Keep your weight centered
</response_format>"""

# --- Fallback Prompts ---

EQUIPMENT_FALLBACK_PROMPT = """\
When asked about equipment, briefly mention that your expertise is in ski instruction, and that is is better 
to consult a ski shop professional who can provide personalized recommendations based on the 
skier's height, weight, skill level, and skiing goals. Be friendly. Keep response under 3 sentences.
Write in plain text only - NO asterisks, NO markdown formatting, NO special characters.
"""

MEDICAL_FALLBACK_PROMPT = """\
You are a safety-focused ski instructor. When someone mentions injury or pain,
immediately redirect them to seek medical attention from a healthcare professional.
Do not give medical advice, since that is not your domain knowledge. Be brief and direct. Keep response under 2 sentences.
Write in plain text only - NO asterisks, NO markdown formatting, NO special characters.
"""

ADVANCED_FALLBACK_PROMPT = """\
You are a beginner ski instructor. When asked about advanced techniques,
briefly explain these are outside your scope and recommend intermediate/advanced lessons.
Be encouraging. Keep response under 3 sentences.
Write in plain text only - NO asterisks, NO markdown formatting, NO special characters.
"""

SKIRESORT_FALLBACK_PROMPT = """\
You are a instructor. When someone asks about where should they ski, briefly explain to them 
that you do not know the specifics of ski resort, and recommend that they to visit the official ski-resort websites or contact them directly."
Keep the response under 3 sentences.
Write in plain text only - NO asterisks, NO markdown formatting, NO special characters.
"""

# --- Examples ---

FEW_SHOT_EXAMPLES = [
    {
        "user": (
            "How do I control my speed while skiing?"
        ),
        "assistant": (
            "Skiing speed can be controlled by skiing across the hill in a zig-zag pattern, rather than straight down."
            "This is called skiing in wedge turns, which is a fundamental technique for beginners." 
            "To do this, point the tips of your skis towards each other to form a wedge shape," ""
            "and then shift your weight to the outer ski to make a turn."
            "To regain the spped, you can straighten your skis and ski down the slope in a straight line, but be careful not to go too fast. "
        ),
    },
    {
        "user": "Can you tell me more about wedge turns?",  # Follow-up asking for more
        "assistant": (
            "Sure! Here's more detail on wedge turns:\n\n"
            "1. Start Position: Stand with skis in a wedge - tips close together, tails pushed apart to form a V shape.\n"
            "2. Turning: To turn right, shift more weight onto your left ski (the outside ski). To turn left, weight your right ski.\n"
            "3. Body Position: Keep your weight forward, knees slightly bent, and hands in front where you can see them.\n\n"
            "Practice on gentle green slopes first, making smooth S-shaped turns down the hill. "
            "This technique will become second nature with practice."
        ),
    },
    {
        "user": (
            "How do I move from wedge (or beginner) turns to (intermediate) parallel skiing?"
        ),
        "assistant": (
            "Moving from wedge turns to parallel skiing is a gradual process that involves refining your technique and building confidence on the slopes. "
            "In parallel skiing, you ski in a circular motion with your skis parallel to each other, instead of in a wedge shape in a zig-zag pattern."
            "Start by practicing your wedge turns and focus on keeping your skis close together while maintaining control. "
            "As you become more comfortable, try to bring your skis closer together during the turns, eventually allowing them to become parallel. "
            "It's important to maintain a balanced stance and keep your weight centered over your skis as you transition to parallel skiing. "
            "Remember to be patient and take it step by step, as mastering parallel skiing takes time and practice."
        ),
    },
    {
        "user": (
            "What kind of skis should I buy as a beginner?"
        ),
        "assistant": (
           "I specialise in ski technique instruction, so I recommend consulting with a professional at a ski shop for equipment recommendations. "
           "Staff at ski shops can help you find the right skis based on your height, weight, skill level, and the type of skiing you plan to do. "
           "It is essential to get proper gear to ensure safety and enjoyment on the slopes, so I encourage you to seek expert advice when it comes to choosing your skis and other equipment."
        ),
    },
]



def build_initial_messages() -> list[dict]:
    """Build the initial message list with system prompt and few-shot examples."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for example in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": example["user"]})
        messages.append({"role": "assistant", "content": example["assistant"]})
    return messages


# --- LLM Call ---


def generate_response(messages: list[dict]) -> str:
    """Generate a response using LiteLLM.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
                  Example: [{"role": "user", "content": "Hello!"}]

    Returns:
        The assistant's response text.
    """
    try:
        response = completion(model=MODEL, messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        return f"Something went wrong: {e}"


# --- Session Management ---

# Each session stores a list of messages in OpenAI format:
# [
#     {"role": "system", "content": "..."},
#     {"role": "user", "content": "Hello!"},
#     {"role": "assistant", "content": "Hi there!"},
#     ...
# ]
sessions: dict[str, list[dict]] = {}

# --- Python Backstop (Claude AI used for assistance) ---

import re

def detect_and_handle_special_cases(user_message: str, session_messages: list[dict]) -> str:
    """
    Detect keywords/patterns in user message and use fallback prompts if needed.
    Returns special response if triggered, None otherwise.
    """
    message_lower = user_message.lower()
    
    # Category 1: Equipment keywords
    equipment_keywords = [
        "buy", "purchase", "rent", "rental", "what skis", "which skis", "ski brand", "ski model",
        "boot", "binding", "pole", "helmet", "gear", "equipment", "ski shop", "what shop"
    ]
    
    # Category 2: Medical/injury keywords (SAFETY)
    medical_keywords = [
        "injury", "hurt", "pain", "ache", "sore", "sprain", "break", 
        "twisted", "doctor", "hospital", "bleeding", "emergency", "ambulance", "ACL",
        'knee', 'wrist', 'shoulder', 'headache', 'concussion'
    ]
    
    # Category 3: Advanced technique keywords
    advanced_keywords = [
        "mogul", "powder", "backcountry", "off-piste", "carving", 
        "racing", "jump", "trick", "park", "black diamond", "double black", "expert run",
        "unmarked run", "steep", "glade", "tree skiing", "compete", "edge control", "dynamic skiing"
    ]
    
    # Category 4: Ski resort keywords (RESORT RECOMMENDATION)
    skiresort_keywords = [
        "resort", "where should i ski", "which mountain", "which hill", "which slope", "where to ski",
        "which ski resort", "which ski mountain", "where can i ski", "cheapest ski resort",
        "best place to ski", "best ski is this country, city, region", "is this ski resort safe"
    ]
    
    # Category 5: Prompt injection
    injection_patterns = [
        r"ignore.*previous",
        r"you are now",
        r"pretend you",
        r"act as (?!a ski|instructor)"
    ]
    
    # Check and handle each category
    if any(keyword in message_lower for keyword in equipment_keywords):
        return _regenerate_with_fallback(user_message, EQUIPMENT_FALLBACK_PROMPT)
    
    if any(keyword in message_lower for keyword in medical_keywords):
        return _regenerate_with_fallback(user_message, MEDICAL_FALLBACK_PROMPT)
    
    if any(keyword in message_lower for keyword in skiresort_keywords):
        return _regenerate_with_fallback(user_message, SKIRESORT_FALLBACK_PROMPT)
    
    if any(keyword in message_lower for keyword in advanced_keywords):
        return _regenerate_with_fallback(user_message, ADVANCED_FALLBACK_PROMPT)
    
    if any(re.search(pattern, message_lower) for pattern in injection_patterns):
        return "I'm a ski instructor for beginners. I can only help with basic skiing technique on groomed runs."
    
    return None  # No special handling needed


def _regenerate_with_fallback(user_message: str, fallback_prompt: str) -> str:
    """Regenerate response using a fallback system prompt."""
    fallback_messages = [
        {"role": "system", "content": fallback_prompt},
        {"role": "user", "content": user_message}
    ]
    
    try:
        response = completion(model=MODEL, messages=fallback_messages)
        return response.choices[0].message.content
    except Exception as e:
        return "I specialize in beginner skiing technique. For questions other than this, please consult an appropriate professional."

# --- FastAPI App ---

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.get("/")
def index():
    return FileResponse("index.html")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        # Start with the system prompt and few-shot examples
        sessions[session_id] = build_initial_messages()

    # Add user message to conversation
    sessions[session_id].append({"role": "user", "content": request.message})

    # PYTHON BACKSTOP: Check for special cases BEFORE generating response
    fallback_response = detect_and_handle_special_cases(
        request.message, 
        sessions[session_id]
    )
    if fallback_response is not None:
        return ChatResponse(response=fallback_response, session_id=session_id)
    # Generate response
    response_text = generate_response(sessions[session_id])

    # Add assistant response to conversation history
    sessions[session_id].append({"role": "assistant", "content": response_text})

    return ChatResponse(response=response_text, session_id=session_id)


@app.post("/clear")
def clear(session_id: str | None = None):
    if session_id and session_id in sessions:
        del sessions[session_id]
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
