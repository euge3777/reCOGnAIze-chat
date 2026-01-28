#!/usr/bin/env python3
"""
ReCOGnAIze Cognitive Health Companion
Pre-Assessment Education & Post-Assessment Guidance Platform

Primary Use Cases:
1. BEFORE Assessment: Risk phenotyping conversation, educate user on VCI
2. AFTER Assessment: Results interpretation, lifestyle guidance, action planning

Research Foundation: Mohammed et al., 2025
"""

import streamlit as st
import json
import sys
import os
import base64
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from recommendation_engine import RecommendationEngine
from domain_chatbot import initialize_chatbot
from file_processor import FileProcessor
from report_summarizer import summarize_report

# Configure Streamlit with logo from assets
logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
favicon_path = os.path.join(os.path.dirname(__file__), 'assets', 'favicon.ico')

st.set_page_config(
    page_title="ReCOGnAIze Cognitive Health Companion",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject favicon from assets using custom HTML in head
if os.path.exists(favicon_path):
    favicon_data = open(favicon_path, 'rb').read()
    b64_favicon = base64.b64encode(favicon_data).decode()
    st.markdown(
        f"""
        <link rel="icon" type="image/x-icon" href="data:image/x-icon;base64,{b64_favicon}">
        """,
        unsafe_allow_html=True
    )

# Custom CSS - Clean, professional design without emojis
st.markdown("""
<style>
    .main-logo {
        max-width: 120px;
        height: auto;
        margin-bottom: 20px;
    }
    .title-main {
        font-size: 2.8em;
        font-weight: 700;
        color: #1a3a52;
        margin-bottom: 5px;
        letter-spacing: -0.5px;
    }
    .subtitle {
        font-size: 1.15em;
        color: #555;
        margin-bottom: 30px;
        font-weight: 500;
    }
    .phase-header {
        font-size: 1.8em;
        font-weight: 700;
        color: #003f87;
        margin: 30px 0 20px 0;
        padding-bottom: 10px;
        border-bottom: 3px solid #0066cc;
    }
    .assessment-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 25px;
        border-radius: 12px;
        margin: 15px 0;
        border-left: 5px solid #003f87;
    }
    .result-card {
        background: #fff;
        padding: 20px;
        border-radius: 10px;
        margin: 12px 0;
        border: 2px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .risk-high {
        background-color: #ffebee;
        border-left: 5px solid #d32f2f;
        color: #c62828;
        font-weight: 600;
    }
    .risk-moderate {
        background-color: #fff3e0;
        border-left: 5px solid #f57c00;
        color: #e65100;
        font-weight: 600;
    }
    .risk-low {
        background-color: #e8f5e9;
        border-left: 5px solid #388e3c;
        color: #2e7d32;
        font-weight: 600;
    }
    .evidence-box {
        background: #f0f4f8;
        padding: 15px;
        border-left: 4px solid #003f87;
        margin: 15px 0;
        border-radius: 5px;
        font-size: 0.95em;
    }
    .action-step {
        background: #fafbfc;
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        border-left: 4px solid #0066cc;
    }
    .pillar-section {
        background: white;
        padding: 25px;
        border-radius: 10px;
        margin: 20px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .metric-box {
        text-align: center;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 10px;
        margin: 10px 0;
    }
    .metric-value {
        font-size: 2em;
        font-weight: 700;
        color: #003f87;
    }
    .metric-label {
        font-size: 0.9em;
        color: #666;
        margin-top: 5px;
    }
    .research-quote {
        font-style: italic;
        border-left: 4px solid #003f87;
        padding-left: 20px;
        margin: 20px 0;
        color: #444;
    }
    .next-steps-box {
        background: #e3f2fd;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #2196f3;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)


def display_logo():
    """Display the logo from assets - on the left side."""
    logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
    if os.path.exists(logo_path):
        st.image(logo_path, width=200, use_container_width=False)


def get_chat_session_dir() -> Path:
    """Return directory path where chat sessions are stored on disk."""
    base_dir = Path(os.path.dirname(__file__)) / "data" / "chat_sessions"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def get_or_create_chat_session_id() -> str:
    """Get chat session ID from URL query params or create a new one.

    This approximates browser-local persistence: as long as the user
    returns to the same URL with the session_id parameter, their
    conversation is restored from disk.
    """
    params = st.query_params

    # Handle both string and list forms for safety
    existing = params.get("session_id") if hasattr(params, "get") else None
    if isinstance(existing, list) and existing:
        return existing[0]
    if isinstance(existing, str) and existing:
        return existing

    session_id = uuid.uuid4().hex
    try:
        # New, non-experimental API for setting query params
        params["session_id"] = session_id
    except Exception:
        # Fallback: best-effort, but don't break the app if this fails
        pass
    return session_id


def load_chat_history(session_id: str) -> None:
    """Load chat history for a given session ID into session_state."""
    session_dir = get_chat_session_dir()
    chat_file = session_dir / f"{session_id}.json"

    if chat_file.exists():
        try:
            with chat_file.open("r", encoding="utf-8") as f:
                messages = json.load(f)
            if isinstance(messages, list):
                st.session_state.chat_messages = messages
        except Exception:
            # If anything goes wrong, start with empty history
            st.session_state.chat_messages = []


def save_chat_history(session_id: str) -> None:
    """Persist current chat history for a given session ID to disk."""
    session_dir = get_chat_session_dir()
    chat_file = session_dir / f"{session_id}.json"

    try:
        with chat_file.open("w", encoding="utf-8") as f:
            json.dump(st.session_state.chat_messages, f, ensure_ascii=False, indent=2)
    except Exception:
        # Persistence failures should not break the app flow
        pass


def ensure_chat_session() -> None:
    """Ensure chat session id and history are initialized in session_state."""
    if 'chat_session_id' not in st.session_state:
        st.session_state.chat_session_id = get_or_create_chat_session_id()

    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
        load_chat_history(st.session_state.chat_session_id)


def initialize_session():
    """Initialize session state variables."""
    if 'engine' not in st.session_state:
        try:
            st.session_state.engine = RecommendationEngine()
        except Exception as e:
            st.error(f"Failed to initialize recommendation engine: {e}")
            st.session_state.engine = None
    
    if 'chatbot' not in st.session_state:
        try:
            st.session_state.chatbot = initialize_chatbot()
        except Exception as e:
            st.error(f"Failed to initialize chatbot: {e}")
            st.session_state.chatbot = None
    
    if 'phase' not in st.session_state:
        st.session_state.phase = 'pre-assessment'  # pre-assessment or post-assessment
    
    if 'conversation_risk' not in st.session_state:
        st.session_state.conversation_risk = 0
    
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None
    
    # Initialize chat persistence (session id + history)
    ensure_chat_session()


def phase_pre_assessment():
    """
    PHASE 1: Pre-Assessment Education & Risk Phenotyping
    User articulates vague concerns, chatbot educates on VCI and recommends assessment
    """
    st.markdown('<div class="phase-header">Cognitive Health Pre-Assessment</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="research-quote">
    "Vascular cognitive impairment accounts for 50-70% of all dementia cases, yet remains underdiagnosed. 
    Early detection and lifestyle intervention can significantly delay progression." 
    - Mohammed et al., 2025
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.subheader("Tell us what brings you here today")
        st.write("Your responses help us understand your cognitive concerns and provide personalized education.")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            age = st.number_input("Age", min_value=18, max_value=120, value=50)
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
        
        with col2:
            family_history = st.multiselect(
                "Family history of cognitive decline?",
                ["Parent", "Sibling", "Grandparent", "No known history"]
            )
        
        st.write("---")
        
        # Conversational risk assessment
        st.subheader("Memory & Cognitive Concerns")
        
        concern1 = st.checkbox("I'm more forgetful lately (recent events, conversations)")
        concern2 = st.checkbox("I struggle with mental speed or quick decision-making")
        concern3 = st.checkbox("I have difficulty organizing or planning complex tasks")
        concern4 = st.checkbox("I'm having trouble staying focused on one task")
        concern5 = st.checkbox("These changes are affecting my daily activities")
        
        # Vascular risk factor assessment
        st.write("---")
        st.subheader("Vascular Risk Factors")
        st.write("VCI is primarily driven by modifiable vascular factors. Research shows managing these slows cognitive decline.")
        
        col1, col2 = st.columns(2)
        with col1:
            hypertension = st.checkbox("High blood pressure (or taking BP medications)")
            high_cholesterol = st.checkbox("High cholesterol (or taking cholesterol medications)")
            diabetes = st.checkbox("Type 2 diabetes (or prediabetes)")
        
        with col2:
            smoking = st.checkbox("Current or former smoker")
            obesity = st.checkbox("BMI over 30")
            sedentary = st.checkbox("Sedentary lifestyle (little regular exercise)")
        
        # Calculate conversational risk score
        cognitive_concerns = sum([concern1, concern2, concern3, concern4, concern5])
        vascular_factors = sum([hypertension, high_cholesterol, diabetes, smoking, obesity, sedentary])
        conversation_risk_score = (cognitive_concerns * 1.5 + vascular_factors * 1.0) / 2
        conversation_risk_score = min(10, conversation_risk_score)  # Cap at 10
        
        st.session_state.conversation_risk = conversation_risk_score
        
        # Display risk assessment
        st.write("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value">{}</div>
                <div class="metric-label">Cognitive Concerns Noted</div>
            </div>
            """.format(cognitive_concerns), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value">{}</div>
                <div class="metric-label">Vascular Risk Factors</div>
            </div>
            """.format(vascular_factors), unsafe_allow_html=True)
        
        with col3:
            risk_class = 'risk-low' if conversation_risk_score < 4 else ('risk-moderate' if conversation_risk_score < 7 else 'risk-high')
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value">{:.1f}/10</div>
                <div class="metric-label">Overall Risk Signal</div>
            </div>
            """.format(conversation_risk_score), unsafe_allow_html=True)
        
        # Educational messaging based on risk
        st.write("---")
        
        if conversation_risk_score >= 7:
            st.markdown("""
            <div class="assessment-card">
            <strong>What This Means:</strong> Your responses indicate several cognitive concerns combined with vascular risk factors. 
            Research shows this pattern can benefit from objective cognitive screening.
            
            The ReCOGnAIze app is a validated, 15-minute digital assessment that:
            - Evaluates processing speed, executive function, and attention (key VCI markers)
            - Generates objective scores you can discuss with your doctor
            - Requires no special equipment - works on any tablet
            
            <strong>Evidence Base:</strong> The SPRINT MIND trial demonstrated that intensive management of blood pressure 
            can significantly reduce cognitive decline. Early identification enables this intervention.
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Proceed to ReCOGnAIze Assessment", type="primary", use_container_width=True):
                st.session_state.phase = 'assessment-input'
                st.rerun()
        
        elif conversation_risk_score >= 4:
            st.markdown("""
            <div class="assessment-card" style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);">
            <strong>Moderate Risk Signal:</strong> You've noted some cognitive concerns and have vascular risk factors. 
            Objective screening could help establish a baseline and identify areas for lifestyle optimization.
            
            <strong>Next Step:</strong> Consider taking the ReCOGnAIze assessment. Even without high risk, baseline 
            measurement allows tracking changes over time - which research shows is more valuable than isolated snapshots.
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Take ReCOGnAIze Assessment", type="primary", use_container_width=True):
                st.session_state.phase = 'assessment-input'
                st.rerun()
        
        else:
            st.markdown("""
            <div class="assessment-card" style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);">
            <strong>Lower Risk Profile:</strong> Your responses suggest fewer immediate cognitive concerns. 
            However, regular cognitive monitoring is recommended for all adults over 50.
            
            <strong>Why Screen?</strong> VCI can progress subtly. A baseline ReCOGnAIze assessment provides:
            - Objective cognitive metrics for future comparison
            - Evidence-based guidance on cognitive health maintenance
            - Early detection if changes occur
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Get Baseline Cognitive Assessment", use_container_width=True):
                st.session_state.phase = 'assessment-input'
                st.rerun()


def phase_assessment_input():
    """PHASE 2: Input ReCOGnAIze assessment results."""
    st.markdown('<div class="phase-header">ReCOGnAIze Assessment Results</div>', unsafe_allow_html=True)
    
    st.write("Enter your ReCOGnAIze assessment scores from the tablet-based test (0-20 composite scale)")
    
    with st.form("assessment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            symbol_matching = st.slider("Symbol Matching (Processing Speed)", 0, 5, 3, 
                                       help="0-5 scale: Lower = slower processing")
            trail_making = st.slider("Trail Making (Executive Function)", 0, 5, 3,
                                    help="0-5 scale: Lower = reduced flexibility")
        
        with col2:
            airplane_game = st.slider("Airplane Game (Attention & Impulse Control)", 0, 5, 3,
                                     help="0-5 scale: Lower = impulse control issues")
            grocery_shopping = st.slider("Grocery Shopping (Memory & Processing)", 0, 5, 3,
                                        help="0-5 scale: Lower = slower real-world processing")
        
        st.write("---")
        st.subheader("Vascular Risk Factors")
        
        col1, col2 = st.columns(2)
        with col1:
            systolic_bp = st.number_input("Current Systolic BP (mmHg)", 90, 200, 130)
            total_cholesterol = st.number_input("Total Cholesterol (mg/dL)", 100, 350, 200)
        
        with col2:
            diabetes = st.selectbox("Diabetes Status", ["None", "Prediabetes", "Type 2", "Type 1"])
            age_input = st.number_input("Age (years)", 18, 120, 55)
        
        st.write("---")
        
        demographics = st.text_input("Any other demographic info (optional, e.g., education level)")
        
        if st.form_submit_button("Generate Personalized Recommendations", type="primary", use_container_width=True):
            st.session_state.phase = 'post-assessment'
            
            # Store assessment data
            st.session_state.assessment_scores = {
                'symbol_matching': symbol_matching,
                'trail_making': trail_making,
                'airplane_game': airplane_game,
                'grocery_shopping': grocery_shopping,
                'composite_score': symbol_matching + trail_making + airplane_game + grocery_shopping,
                'systolic_bp': systolic_bp,
                'total_cholesterol': total_cholesterol,
                'diabetes': diabetes,
                'age': age_input
            }
            st.rerun()


def phase_post_assessment():
    """PHASE 3: Post-Assessment Results Interpretation & Guidance."""
    st.markdown('<div class="phase-header">Your Results & Personalized Guidance</div>', unsafe_allow_html=True)
    
    scores = st.session_state.assessment_scores
    
    # Results Summary
    st.subheader("Assessment Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{scores['composite_score']:.1f}</div>
            <div class="metric-label">Composite Score (0-20)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{scores['age']}</div>
            <div class="metric-label">Age (years)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{scores['systolic_bp']}</div>
            <div class="metric-label">Systolic BP (mmHg)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{scores['diabetes']}</div>
            <div class="metric-label">Diabetes Status</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("---")
    
    # Domain-by-domain explanation
    st.subheader("Understanding Your Scores by Cognitive Domain")
    
    domains = [
        {
            'name': 'Processing Speed',
            'score': scores['symbol_matching'],
            'game': 'Symbol Matching',
            'description': 'How quickly you perceive and respond to information',
            'vci_connection': 'Key VCI biomarker - slowed processing is characteristic of cerebrovascular disease',
            'age_norm': 2.8 if scores['age'] < 65 else 2.4
        },
        {
            'name': 'Executive Function',
            'score': scores['trail_making'],
            'game': 'Trail Making',
            'description': 'Your ability to plan, organize, and shift between tasks',
            'vci_connection': 'Executive dysfunction reflects frontal-subcortical circuit disruption from small vessel disease',
            'age_norm': 3.1 if scores['age'] < 65 else 2.7
        },
        {
            'name': 'Attention & Impulse Control',
            'score': scores['airplane_game'],
            'game': 'Airplane Game',
            'description': 'Your ability to focus and inhibit inappropriate responses',
            'vci_connection': 'Impulse dyscontrol is a significant behavioral manifestation in high cerebrovascular burden',
            'age_norm': 3.2 if scores['age'] < 65 else 2.8
        },
        {
            'name': 'Memory & Processing',
            'score': scores['grocery_shopping'],
            'game': 'Grocery Shopping',
            'description': 'Real-world memory function and processing efficiency',
            'vci_connection': 'Slower task completion reflects reduced processing speed and efficiency',
            'age_norm': 2.9 if scores['age'] < 65 else 2.5
        }
    ]
    
    for domain in domains:
        score_level = 'Low' if domain['score'] < 2 else ('Medium' if domain['score'] < 3.5 else 'High')
        comparison = 'below' if domain['score'] < domain['age_norm'] else 'above'
        
        with st.container():
            st.markdown(f"""
            <div class="result-card">
            <strong>{domain['name']}</strong>
            <br>Your Score: {domain['score']:.1f}/5 | Age-Adjusted Norm: {domain['age_norm']:.1f}/5 ({comparison} average)
            <br><em>{domain['description']}</em>
            </div>
            """, unsafe_allow_html=True)
            
            if domain['score'] < domain['age_norm']:
                st.markdown(f"""
                <div class="evidence-box">
                <strong>What This Means:</strong> {domain['vci_connection']}
                <br><br>This is not a diagnosis, but a measurement highlighting an area that may benefit from:
                1. Discussion with your healthcare provider about vascular risk factors
                2. Lifestyle modifications supported by research (see guidance below)
                3. Repeat assessment in 6-12 months to track changes
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="evidence-box" style="border-left: 4px solid #388e3c;">
                <strong>Strong Performance:</strong> Your {domain['name'].lower()} is at or above age-typical levels. 
                Continue current cognitive health practices.
                </div>
                """, unsafe_allow_html=True)
    
    st.write("---")
    
    # Vascular Context
    st.subheader("Your Vascular Risk Profile")
    
    vascular_insights = []
    
    if scores['systolic_bp'] >= 140:
        vascular_insights.append("Hypertension (>140 mmHg systolic) significantly accelerates cognitive decline. SPRINT MIND trial showed intensive BP control (<120 mmHg) reduces progression.")
    elif scores['systolic_bp'] >= 130:
        vascular_insights.append("BP is elevated. Research recommends target <120 mmHg for cognitive protection. Discuss with your doctor.")
    else:
        vascular_insights.append("Blood pressure is well-controlled.")
    
    if scores['total_cholesterol'] >= 240:
        vascular_insights.append("High cholesterol (>240 mg/dL) is a VCI risk factor. 60% of VCI patients have hyperlipidemia vs 35% without VCI.")
    elif scores['total_cholesterol'] >= 200:
        vascular_insights.append("Cholesterol is borderline. Lifestyle modifications (diet, exercise) can help.")
    else:
        vascular_insights.append("Cholesterol levels are healthy.")
    
    if scores['diabetes'] != "None":
        vascular_insights.append("Diabetes status affects cognitive outcomes. Tight glucose control supports brain health.")
    else:
        vascular_insights.append("No diabetes. Continue preventive lifestyle habits.")
    
    for insight in vascular_insights:
        st.info(insight)
    
    st.write("---")
    
    # Evidence-Based Next Steps
    st.subheader("Evidence-Based Recommendations")
    
    st.markdown("""
    <div class="next-steps-box">
    <strong>Discuss With Your Healthcare Provider:</strong>
    <br><br>
    1. Share your ReCOGnAIze scores - they highlight VCI-specific cognitive domains often missed by traditional tests
    2. Evaluate vascular risk factors:
       - Blood pressure target: <120 mmHg systolic (SPRINT MIND evidence)
       - Lipid panel review and management if elevated
       - Glucose control if diabetic
    3. Ask about additional neuropsychological testing if indicated
    4. Discuss medication review (some medications impair cognition)
    </div>
    """, unsafe_allow_html=True)
    
    # Lifestyle Recommendations
    st.subheader("Lifestyle Modifications (Research-Backed)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Cardiovascular Health:**
        - Aerobic exercise: 150 min/week moderate intensity
        - Blood pressure control (target <120 mmHg)
        - Mediterranean or DASH diet
        - Limit sodium to <2,300 mg daily
        - Manage cholesterol through diet and/or medication
        """)
    
    with col2:
        st.markdown("""
        **Cognitive Engagement:**
        - Mental stimulation: learning, puzzles, reading
        - Social engagement and group activities
        - Cognitive training (typing, language learning)
        - Sleep optimization: 7-8 hours nightly
        - Stress management: meditation, yoga
        """)
    
    st.write("---")
    
    # Monitoring Plan
    st.subheader("Your Cognitive Health Monitoring Plan")
    
    st.markdown("""
    <div class="action-step">
    <strong>BASELINE (Today):</strong> You now have objective cognitive metrics as a reference point.
    </div>
    
    <div class="action-step">
    <strong>3 MONTHS:</strong> Implement lifestyle changes. Reassess vascular risk factors with your doctor.
    </div>
    
    <div class="action-step">
    <strong>6 MONTHS:</strong> Repeat ReCOGnAIze assessment to see if scores are stable, improving, or declining.
    Tracking changes over time is more valuable than single snapshots.
    </div>
    
    <div class="action-step">
    <strong>12 MONTHS:</strong> Full reassessment. Adjust interventions based on progress.
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    # Export Data
    st.subheader("Export Your Results")
    
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'assessment_scores': scores,
        'domains': domains,
        'vascular_insights': vascular_insights
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        json_export = json.dumps(export_data, indent=2)
        st.download_button(
            label="Download Results (JSON)",
            data=json_export,
            file_name=f"recognaize_results_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    with col2:
        if st.button("Start New Assessment", use_container_width=True):
            st.session_state.phase = 'pre-assessment'
            st.session_state.assessment_scores = None
            st.rerun()
    
    st.write("---")
    st.markdown("""
    **Research Reference:**
    Mohammed, A.A., et al. (2025). ReCOGnAIze app to detect vascular cognitive impairment and mild cognitive impairment. 
    Alzheimer's & Dementia. https://doi.org/10.1002/alz.70992
    """)


def chatbot_interface():
    """
    CHATBOT: Domain-focused Q&A about cognitive health and vascular risk management
    """
    st.markdown('<div class="phase-header">Cognitive Health Assistant</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Ask questions about cognitive health, vascular cognitive impairment, lifestyle interventions, 
    or any related topics. The assistant has access to evidence-based information from the ReCOGnAIze 
    research study and validated health frameworks.
    """)
    
    # Display uploaded files info
    if 'uploaded_files' in st.session_state and st.session_state.uploaded_files:
        file_list = ", ".join([f["filename"] for f in st.session_state.uploaded_files])
        st.info(f"📎 **Files loaded in context:** {file_list}")
    
    if st.session_state.chatbot is None:
        st.error("Chatbot failed to initialize. Please refresh the page.")
        return
    
    # Display chat history
    # Show previous messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])
    
    # Input area
    # Style the file uploader so the dropzone is compact
    # and uses the custom SVG icon from assets/upload.svg.
    st.markdown("""
    <style>
    [data-testid="stFileUploadDropzone"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        width: 40px !important;
        height: 40px !important;
        margin: 0 auto !important;
    }
    /* Hide the default text/content but keep the input clickable */
    [data-testid="stFileUploadDropzone"] > div:first-child {
        opacity: 0 !important;
    }
    /* Show the custom upload SVG as the visual button */
    [data-testid="stFileUploadDropzone"]::before {
        content: "";
        display: block;
        width: 40px;
        height: 40px;
        background-image: url("assets/upload.svg");
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.85, 0.065, 0.085])
    
    with col1:
        user_input = st.text_input(
            "Ask a question about cognitive health:",
            placeholder="e.g., How does high blood pressure affect cognitive health? What's the DASH diet?",
            key="chatbot_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Send", help="Send message")
    
    with col3:
        uploaded_files = st.file_uploader(
            "Upload",
            accept_multiple_files=True,
            type=['txt', 'pdf', 'csv', 'json', 'xlsx', 'xls'],
            key='chatbot_file_uploader',
            label_visibility="collapsed"
        )
        if uploaded_files:
            # Initialize file storage in session state if needed
            if 'uploaded_files' not in st.session_state:
                st.session_state.uploaded_files = []
            
            # Process new files
            for uploaded_file in uploaded_files:
                existing_filenames = [f['filename'] for f in st.session_state.uploaded_files]
                if uploaded_file.name not in existing_filenames:
                    try:
                        file_data = FileProcessor.process_uploaded_file(uploaded_file)
                        if file_data:
                            # If this is a PDF report, run the
                            # multi-step summarization pipeline and
                            # keep only the overall summary as the
                            # content injected into the chat model.
                            if file_data.get("file_type") == ".pdf" and file_data.get("content"):
                                with st.spinner(f"Summarizing {uploaded_file.name} for chat context..."):
                                    try:
                                        summary_data = summarize_report(
                                            file_data["content"],
                                            target_chunks=6,
                                        )
                                        # Preserve full extracted text
                                        # for debugging/inspection.
                                        file_data["raw_content"] = file_data["content"]
                                        file_data["chunk_summaries"] = summary_data.get("chunk_summaries", [])
                                        file_data["summary"] = summary_data.get("overall_summary", "")
                                        if file_data["summary"]:
                                            file_data["content"] = file_data["summary"]
                                    except Exception:
                                        st.warning(
                                            f"Could not summarize {uploaded_file.name}; using extracted text instead."
                                        )

                            st.session_state.uploaded_files.append(file_data)
                            st.success(f"{uploaded_file.name} uploaded")
                    except Exception:
                        st.error(f"Error processing {uploaded_file.name}")
    
    # Process user input
    if send_button and user_input:
        # Build augmented prompt with file context
        augmented_input = user_input
        files_included = False
        
        # Store for debug display
        st.session_state.last_augmented_input = None
        
        if 'uploaded_files' in st.session_state and st.session_state.uploaded_files:
            try:
                augmented_input += "\n\n" + "="*60
                augmented_input += "\n[CONTEXT FROM UPLOADED FILES]\n"
                augmented_input += "="*60 + "\n\n"
                
                for file_data in st.session_state.uploaded_files:
                    formatted_content = FileProcessor.format_file_content_for_prompt(file_data)
                    augmented_input += formatted_content + "\n\n"
                    files_included = True
                
                augmented_input += "="*60 + "\n"
                augmented_input += "[END OF FILE CONTEXT]\n"
                augmented_input += "="*60
                st.session_state.last_augmented_input = augmented_input
            except Exception as e:
                st.warning(f"Could not include file context: {str(e)}")
                # Continue with original input if file processing fails
        
        # Add user message to history
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input
        })
        # Persist updated history
        if 'chat_session_id' in st.session_state:
            save_chat_history(st.session_state.chat_session_id)
        
        # Check domain relevance
        is_relevant = st.session_state.chatbot.check_domain_relevance(user_input)

        # If the user has uploaded a ReCOGnAIze report, allow more generic
        # questions like "tell me more about my results" to pass through
        # even if they don't contain explicit domain keywords.
        has_uploaded_files = bool(st.session_state.get('uploaded_files'))

        if not is_relevant and not has_uploaded_files:
            response = """I'm designed to answer questions about cognitive health, vascular cognitive impairment (VCI), 
    brain-protective lifestyle interventions, and related topics. Your question seems to be outside this domain.

    Could you rephrase your question to focus on:
    - Cognitive health and brain function
    - Vascular risk factors and their impact on cognition
    - Lifestyle interventions (diet, exercise, sleep)
    - ReCOGnAIze assessment and VCI understanding

    Feel free to ask again!"""
        else:
            # Generate response with knowledge base context and file context
            with st.spinner("Thinking..."):
                if files_included:
                    st.info("Using uploaded file context in this response")
                response = st.session_state.chatbot.generate_response(
                    augmented_input,
                    conversation_history=st.session_state.chat_messages[:-1]  # Exclude the just-added user message
                )
        
        # Add assistant response to history
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response
        })
        # Persist updated history
        if 'chat_session_id' in st.session_state:
            save_chat_history(st.session_state.chat_session_id)
        
        # Force rerun to display new messages
        st.rerun()
    
    # Clear buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Conversation", help="Start a new conversation", use_container_width=True):
            st.session_state.chat_messages = []
            # Also clear persisted history for this session
            if 'chat_session_id' in st.session_state:
                session_dir = get_chat_session_dir()
                chat_file = session_dir / f"{st.session_state.chat_session_id}.json"
                try:
                    if chat_file.exists():
                        chat_file.unlink()
                except Exception:
                    pass
            st.rerun()
    
    with col2:
        if 'uploaded_files' in st.session_state and st.session_state.uploaded_files:
            if st.button("Clear Uploaded Files", help="Remove all files from context", use_container_width=True):
                st.session_state.uploaded_files = []
                st.rerun()


def main():
    """Main application."""
    
    initialize_session()
    
    # Header with logo on the left
    col_logo, col_spacer = st.columns([0.2, 0.8])
    
    with col_logo:
        display_logo()
    
    st.markdown('<div class="title-main" style="text-align: center;">ReCOGnAIze Cognitive Health Companion</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle" style="text-align: center;">AI-Powered Pre & Post Assessment Education for Vascular Cognitive Health</div>', unsafe_allow_html=True)
    
    st.write("---")
    
    # Navigation tabs (Ask Assistant first, then Assessment)
    tab1, tab2 = st.tabs(["Ask Assistant", "Assessment"])
    
    with tab1:
        chatbot_interface()
    
    with tab2:
        # Route to appropriate assessment phase
        if st.session_state.phase == 'pre-assessment':
            phase_pre_assessment()
        
        elif st.session_state.phase == 'assessment-input':
            phase_assessment_input()
        
        elif st.session_state.phase == 'post-assessment':
            phase_post_assessment()
    
    # Debug sidebar - Show what's being sent to the model
    with st.sidebar:
        st.divider()
        with st.expander("🔍 View Context Sent to Model", expanded=False):
            if 'last_augmented_input' in st.session_state and st.session_state.last_augmented_input:
                st.subheader("Full Augmented Prompt")
                st.text_area(
                    "This is what the chatbot receives (your question + file context):",
                    value=st.session_state.last_augmented_input,
                    height=250,
                    disabled=True
                )
                
                # Show stats
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Characters", len(st.session_state.last_augmented_input))
                with col2:
                    st.metric("Approx Tokens", len(st.session_state.last_augmented_input) // 4)
                
                # Check if file context is included
                if "[CONTEXT FROM UPLOADED FILES]" in st.session_state.last_augmented_input:
                    st.success("✓ File context included & sent to model")
                else:
                    st.warning("ℹ No file context in this prompt")

                # Offer a JSON download of the payload that the model sees
                messages_payload = {
                    "system": getattr(st.session_state.chatbot, "system_prompt", ""),
                    "conversation_history": st.session_state.chat_messages[:-1] if st.session_state.get("chat_messages") else [],
                    "user_augmented_input": st.session_state.last_augmented_input,
                }

                json_str = json.dumps(messages_payload, ensure_ascii=False, indent=2)
                st.download_button(
                    label="Download JSON of model input",
                    data=json_str,
                    file_name="model_input_debug.json",
                    mime="application/json"
                )
            else:
                st.info("💡 Send a message to see what's being sent to the model.")
    
    # Footer
    st.write("---")
    st.markdown("""
    **About ReCOGnAIze:**
    ReCOGnAIze is a validated digital cognitive assessment that detects vascular cognitive impairment (VCI) 
    with 85% accuracy. VCI accounts for 50-70% of dementia cases but is often underdiagnosed. This companion 
    app educates users before assessment and guides interpretation afterward, facilitating meaningful 
    conversations with healthcare providers about cognitive health and vascular risk management.
    """)


if __name__ == "__main__":
    main()
