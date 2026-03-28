"""
🤖 AI Engine - Multi API Resume Updater
APIs: Groq → Gemini (New SDK) → OpenRouter → Cohere → HuggingFace
If one fails, automatically tries the next!

Updated: Migrated to Google GenAI SDK
"""

# ============ IMPORT API KEYS ============
from config import (
    GROQ_API_KEY,
    GEMINI_API_KEY,
    OPENROUTER_API_KEY,
    COHERE_API_KEY,
    HUGGINGFACE_API_KEY
)


# ============ API 1: GROQ (Fastest) ============
def try_groq(prompt):
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer and career advisor."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=3000
        )
        result = response.choices[0].message.content
        if result:
            return result
        return None
    except Exception as e:
        print(f"❌ Groq failed: {e}")
        return None


# ============ API 2: GEMINI (New GenAI SDK) ============
def try_gemini(prompt):
    try:
        from google import genai
        from google.genai import types

        # Create client with API key
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Generate content using new SDK format
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=3000,
                system_instruction="You are an expert resume writer and career advisor."
            )
        )

        if response.text:
            return response.text
        return None
    except Exception as e:
        print(f"❌ Gemini failed: {e}")
        return None


# ============ API 3: OPENROUTER ============
def try_openrouter(prompt):
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )

        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer and career advisor."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=3000
        )
        result = response.choices[0].message.content
        if result:
            return result
        return None
    except Exception as e:
        print(f"❌ OpenRouter failed: {e}")
        return None


# ============ API 4: COHERE ============
def try_cohere(prompt):
    try:
        import cohere
        co = cohere.ClientV2(api_key=COHERE_API_KEY)

        response = co.chat(
            model="command-r-plus",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer and career advisor."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        result = response.message.content[0].text
        if result:
            return result
        return None
    except Exception as e:
        print(f"❌ Cohere failed: {e}")
        return None


# ============ API 5: HUGGINGFACE ============
def try_huggingface(prompt):
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(api_key=HUGGINGFACE_API_KEY)

        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer and career advisor."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=3000
        )
        result = response.choices[0].message.content
        if result:
            return result
        return None
    except Exception as e:
        print(f"❌ HuggingFace failed: {e}")
        return None


# ============ SMART FALLBACK FUNCTION ============
def get_ai_response(prompt):
    """
    Tries all APIs one by one.
    If one fails → automatically tries next!
    """

    apis = [
        ("🟢 Groq", try_groq),
        ("🔵 Gemini", try_gemini),
        ("🟠 OpenRouter", try_openrouter),
        ("🟡 Cohere", try_cohere),
        ("🟣 HuggingFace", try_huggingface),
    ]

    for name, api_func in apis:
        print(f"⏳ Trying {name}...")
        result = api_func(prompt)

        if result:
            print(f"✅ {name} success!")
            return result
        else:
            print(f"⚠️ {name} failed, trying next...")

    return "❌ All APIs failed. Please try again later."


# ============ RESUME FUNCTIONS ============

def analyze_resume(resume_text, jd_text):
    """Analyze resume against JD"""
    prompt = f"""
You are an expert resume analyst.

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

Analyze and provide:

1. 📊 **Match Score**: ___ / 100%

2. ✅ **Matching Skills**:
   - List each matching skill

3. ❌ **Missing Skills**:
   - List each missing skill from JD

4. 🔑 **Missing Keywords**:
   - Important keywords to add in resume

5. 💡 **Suggestions**:
   - Specific improvements to make

Keep it clear, organized, and use emojis.
"""
    return get_ai_response(prompt)


def update_resume(resume_text, jd_text):
    """Update resume to match JD"""
    prompt = f"""
You are a professional resume writer.

CURRENT RESUME:
{resume_text}

TARGET JOB DESCRIPTION:
{jd_text}

TASK: Rewrite and update the resume to match this job description.

STRICT RULES:
1. Keep ALL true information (name, contact, education, experience, projects)
2. Do NOT invent or add fake skills, experience, or projects
3. Rewrite the Professional Summary to align with JD requirements
4. Reorder Technical Skills — put JD-relevant skills FIRST
5. Rewrite experience bullet points using keywords from JD
6. Rewrite project descriptions using relevant JD terminology
7. Add missing relevant keywords naturally throughout the resume
8. Use strong action verbs (Developed, Implemented, Designed, Optimized, etc.)
9. Make it ATS-friendly (clean formatting, standard section headers)
10. Keep the resume to ONE page length

OUTPUT FORMAT:
Return the complete updated resume with these sections:
- Full Name & Contact Information
- Professional Summary
- Professional Experience (with bullet points)
- Education
- Projects (with bullet points)
- Technical Skills
- Soft Skills
- Languages

Make it ready to use — clean and professional.
"""
    return get_ai_response(prompt)


def generate_cover_letter(resume_text, jd_text):
    """Generate a cover letter"""
    prompt = f"""
You are a professional cover letter writer.

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

Write a professional cover letter following these rules:
1. Length: 250-300 words
2. Match resume skills to JD requirements
3. Show genuine enthusiasm for the role
4. Professional but warm tone
5. Include proper greeting and closing
6. Mention specific company/role details from JD
7. Highlight 2-3 most relevant achievements
8. End with a strong call to action

Format it properly as a letter.
"""
    return get_ai_response(prompt)


def generate_interview_questions(jd_text):
    """Generate interview questions from JD"""
    prompt = f"""
You are an interview preparation expert.

JOB DESCRIPTION:
{jd_text}

Generate the following:

🎯 **10 Most Likely Interview Questions:**
(Number each question)

For each question provide:
- The question
- ✅ Brief ideal answer hint (2-3 lines)

Then add:

💡 **5 General Tips for This Interview**

Format it clearly with emojis and numbering.
"""
    return get_ai_response(prompt)