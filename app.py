"""Main app for CS 101 Assignment Grader."""
import streamlit as st

# Load the grader
import plotly.graph_objects as go
from grader import grade_assignment
import zipfile
import io

# Set page config
st.set_page_config(page_title="CS 101 Assignment Grader", page_icon="🎓", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #2e6da4;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        transition-duration: 0.4s;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #204d74;
    }
    .stTextInput>div>div>input {
        background-color: #f8f9fa;
    }
    .stProgress>div>div>div>div {
        background-color: #4CAF50;
    }
    .small-font {
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

def display_grading_result(result, max_points):
    # Main columns
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        # Score
        st.subheader("Final Score")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=result['final_score'],
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, max_points], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#4CAF50"},
                'steps': [
                    {'range': [0, max_points*0.6], 'color': "lightgray"},
                    {'range': [max_points*0.6, max_points*0.8], 'color': "gray"}]
            }))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Overall Assessment
        st.subheader("Overall Assessment")
        st.write(result["overall_assessment"], className="small-font")

    with col3:
        # Point Deductions
        st.subheader("Point Deductions")
        fig = go.Figure(data=[go.Pie(labels=[d['reason'] for d in result["point_deductions"]], 
                                     values=[d['points'] for d in result["point_deductions"]], 
                                     hole=.3)])
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

    # Code Analysis
    with st.expander("🔍 Code Analysis", expanded=True):
        analysis_col1, analysis_col2 = st.columns(2)
        with analysis_col1:
            st.subheader("Syntax Check")
            if result["syntax_check"]:
                for error in result["syntax_check"]:
                    st.error(f"Line {error['line']}: {error['error']}")
            else:
                st.success("No syntax errors found.")

            st.subheader("Compilation Test")
            if result["compilation_test"]["compiles"]:
                st.success("Code compiles successfully.")
            else:
                st.error("Compilation errors found:")
                for error in result["compilation_test"]["errors"]:
                    st.write(f"- {error}")

        with analysis_col2:
            st.subheader("Logical Errors")
            if result["logical_errors"]:
                for error in result["logical_errors"]:
                    st.warning(error)
            else:
                st.success("No logical errors detected.")

            st.subheader("Runtime Simulation")
            runtime_status = result["runtime_simulation"]["status"]
            runtime_info = f"Status: {runtime_status.capitalize()}\n\nSummary: {result['runtime_simulation']['summary']}\n\nDetails: {result['runtime_simulation']['details']}"
            if runtime_status == "success":
                st.success(runtime_info)
            elif runtime_status == "warning":
                st.warning(runtime_info)
            else:
                st.error(runtime_info)

    # Requirements Assessment
    st.header("📋 Requirements Assessment")
    for req in result["requirements_assessment"]:
        st.markdown(f"{'✅' if req['met'] else '❌'} **{req['requirement']}**")
        st.write(f"Explanation: {req['explanation']}")

    # Extra Credit and Comment Consideration
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🌟 Extra Credit")
        if result["extra_credit"]["awarded"]:
            st.success(f"+{result['extra_credit']['points']} points: {result['extra_credit']['reason']}")
        else:
            st.info("No extra credit awarded.")

    with col2:
        st.subheader("💬 Comment Consideration")
        st.info(result["comment_consideration"])

    # Code Quality and Improvement Suggestions
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔍 Code Quality and Style")
        st.write(result["code_quality"])

    with col2:
        st.subheader("💡 Suggestions for Improvement")
        for suggestion in result["improvement_suggestions"]:
            st.success(suggestion)

def main():
    st.title("🎓 CS 101 Assignment Grader")
    st.info("A comprehensive tool for grading Java assignments, providing detailed analysis, feedback, and scoring based on customizable requirements.")

    # Assignment requirements file upload
    requirements_file = st.file_uploader("Upload assignment requirements", type="txt")

    # Create two columns for file upload and student comment
    col1, col2 = st.columns(2)

    with col1:
        # Java file or zip file upload
        uploaded_file = st.file_uploader("Upload the student's Java file or a .zip file", type=["java", "zip"])

    with col2:
        # Student comment
        student_comment = st.text_area("Student Comment (Optional)", height=150)

    # Maximum points slider
    max_points = st.slider("Maximum Points", min_value=10, max_value=200, value=100, step=5)

    if uploaded_file is not None and requirements_file is not None:
        assignment_guidelines = requirements_file.getvalue().decode("utf-8")
        files = []

        if uploaded_file.type == "application/zip":
            with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith(".java"):
                        with zip_ref.open(file_info) as file:
                            files.append((file_info.filename, file.read().decode("utf-8")))
        else:
            files.append((uploaded_file.name, uploaded_file.getvalue().decode("utf-8")))

        with st.expander("View Uploaded Code"):
            for file_name, content in files:
                st.subheader(file_name)
                st.code(content, language="java")

        with st.expander("View Assignment Requirements"):
            st.text(assignment_guidelines)

        if st.button("Grade Assignment"):
            with st.spinner("Grading in progress..."):
                grade_result = grade_assignment(files, assignment_guidelines, student_comment, max_points)
                st.balloons()
                display_grading_result(grade_result, max_points)

if __name__ == "__main__":
    main()
