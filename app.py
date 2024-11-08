import streamlit as st
import replicate
import os
import speech_recognition as sr
from gtts import gTTS
import tempfile
import time

# App title
st.set_page_config(page_title="Magical toys")

# Custom CSS for background color and glow effect
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(to bottom right, #722f37, #ffffff);
    }
    .glow-on-hover {
        width: 220px; height: 50px; border: none; outline: none; color: #fff;
        background: #111; cursor: pointer; position: relative; z-index: 0;
        transition: color 0.4s, border-color 0.4s, box-shadow 0.4s;
    }
    .glow-on-hover:before {
        content: ''; background: linear-gradient(45deg, #ff0000, #ff7300,
        #fffb00, #48ff00, #38fff7, #3136f8, #9236f8);
        position: absolute; top: -2px; left: -2px; right: -2px; bottom: -2px;
        z-index: -1; filter: blur(4px); opacity: 0.7;
        transition: opacity 0.4s, filter 0.4s;
    }
    .glow-on-hover:hover {
        color: #fff; border-color: #ffffff;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    }
    @keyframes wave {
        0% { transform: translateX(0); }
        50% { transform: translateX(10px); }
        100% { transform: translateX(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    .fade-in-text {
        animation: fadeIn 2s ease-in-out;
    }
    .wave-text {
        animation: wave 2s infinite;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Replicate Credentials
with st.sidebar:
    st.title('Magical toys')
    st.write(
        'This chatbot is created using the open-source Llama 2 LLM model from Meta.')
    if 'REPLICATE_API_TOKEN' in st.secrets:
        st.success('API key already provided!', icon='✅')
        replicate_api = st.secrets['REPLICATE_API_TOKEN']
    else:
        replicate_api = st.text_input(
            'Enter Replicate API token:', type='password')
        if not (replicate_api.startswith('r8_') and len(replicate_api) == 40):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')
    os.environ['REPLICATE_API_TOKEN'] = replicate_api

    st.subheader('Models and parameters')
    selected_model = st.selectbox('Choose a Llama2 model', [
                                  'Llama2-7B', 'Llama2-13B'], key='selected_model')
    if selected_model == 'Llama2-7B':
        llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
    elif selected_model == 'Llama2-13B':
        llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
    temperature = st.sidebar.slider(
        'temperature', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
    top_p = st.sidebar.slider('top_p', min_value=0.01,
                              max_value=1.0, value=0.9, step=0.01)
    max_length = st.sidebar.slider(
        'max_length', min_value=32, max_value=128, value=120, step=8)

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to Magical Bot"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(
            f"<p class='fade-in-text'>{message['content']}</p>", unsafe_allow_html=True)
        if message["role"] == "assistant":
            st.button('🔊 Listen', key=message["content"],
                      on_click=lambda text=message["content"]: play_text_to_speech(text))


def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": "How may I assist you today?"}]


st.sidebar.button('Clear Chat History', on_click=clear_chat_history)


def generate_llama2_response(prompt_input):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    output = replicate.run('a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5',
                           input={"prompt": f"{string_dialogue} {prompt_input} Assistant: ",
                                  "temperature": temperature, "top_p": top_p, "max_length": max_length, "repetition_penalty": 1})
    return output


def listen_to_voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.session_state.is_listening = True
        with st.spinner("Listening..."):
            audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                st.error("Sorry, I did not understand that.")
            except sr.RequestError:
                st.error(
                    "Sorry, there was a problem with the speech recognition service.")
    st.session_state.is_listening = False
    return ""

# Function to convert text to speech using gTTS


def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmpfile:
        tts.save(tmpfile.name)
        return tmpfile.name

# Play text-to-speech audio


def play_text_to_speech(text):
    audio_file = text_to_speech(text)
    st.audio(audio_file, format='audio/mp3')


if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False

st.sidebar.subheader('Voice Input')
if st.sidebar.button('🎙️ Start Recording', key='start-recording',
                     on_click=lambda: st.session_state.update({"recording": True, "is_listening": True})):
    with st.spinner("Recording..."):
        voice_input = listen_to_voice_input()
        if voice_input:
            st.session_state.messages.append(
                {"role": "user", "content": voice_input})
            with st.chat_message("user"):
                st.markdown(
                    f"<p class='wave-text'>{voice_input}</p>", unsafe_allow_html=True)

if st.sidebar.button('🛑 Stop Recording', key='stop-recording',
                     on_click=lambda: st.session_state.update({"recording": False, "is_listening": False})):
    st.session_state.recording = False
    st.session_state.is_listening = False

if st.session_state.is_listening:
    st.sidebar.markdown(
        '<div style="text-align: center;">🎤 <b>Recording...</b></div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown(
        '<div style="text-align: center;">🎙️ <b>Ready to record</b></div>', unsafe_allow_html=True)

# User-provided prompt
if prompt := st.chat_input(disabled=not replicate_api):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(
            '<script src="https://cdn.jsdelivr.net/npm/canvas-confetti"></script><script>canvasConfetti()</script>', unsafe_allow_html=True)

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            progress = st.progress(0)
            for i in range(100):
                progress.progress(i + 1)
            response = generate_llama2_response(prompt)
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(
                    f"<p class='fade-in-text'>{full_response}</p>", unsafe_allow_html=True)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)

    # Display the response with a listen button
    st.chat_message("assistant").button(
        '🔊 Listen', on_click=lambda: play_text_to_speech(full_response))

# Add balloon animation
st.balloons()
