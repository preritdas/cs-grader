# CS 101 Assignment Grader

The CS 101 Assignment Grader is a comprehensive tool designed to automate the grading process for Java programming assignments. It utilizes the o1-preview model from OpenAI to analyze student code, provide detailed feedback, and assign scores based on customizable criteria. This system is designed specifically for CS 101 (Intro to Computer Science), taught in Java (so we must of course grade it using Python). :)

## Key Features

1. **Automated Grading**: Analyzes Java code using the o1-preview model and provides a detailed assessment.
2. **Customizable Criteria**: Allows instructors to set specific grading requirements.
3. **Detailed Feedback**: Offers insights on syntax, logic, runtime behavior, and code quality.
4. **Interactive UI**: Built with Streamlit for an easy-to-use web interface.
5. **Flexible Scoring**: Supports variable maximum points and extra credit.

## How It Works

### 1. Grading Module (`grader.py`)

The core functionality is implemented in `grader.py`:

- **OpenAI Integration**: Uses the o1-preview model via the OpenAI API to analyze code and generate grading results.
- **Prompt Engineering**: Constructs a detailed prompt for the AI model, including assignment guidelines, student code, and grading criteria.
- **JSON Parsing**: Extracts and processes the AI's response into a structured format.
- **Error Handling**: Implements robust error checking and logging.

### 2. Web Interface (`app.py`)

The user interface is built with Streamlit in `app.py`:

- **File Upload**: Allows uploading of Java files and assignment requirement documents.
- **Input Fields**: Provides areas for student comments and setting maximum points.
- **Result Display**: Presents grading results in an organized, visually appealing manner.
- **Interactive Elements**: Uses expandable sections and charts for detailed breakdowns.

### 3. Grading Process

1. **Input Collection**: 
   - User uploads a Java file containing the student's code.
   - Assignment requirements are uploaded as a separate text file.
   - Optional student comments can be added.
   - Maximum points are set using a slider (default 100, range 10-200).

2. **AI Analysis**: The system sends the code, requirements, and grading criteria to the o1-preview model for analysis.

3. **Result Processing**: AI's response is parsed and structured into various assessment categories.

4. **Display**: 
   - Results are presented in the web interface with various sections and visualizations.
   - A gauge chart shows the final score out of the maximum points.
   - A pie chart displays point deductions by category.
   - Detailed breakdowns are provided for code analysis, requirements assessment, and improvement suggestions.

## Key Components

- **Syntax Check**: Identifies syntax errors in the code.
- **Compilation Test**: Assesses if the code would compile successfully.
- **Logical Error Detection**: Analyzes the code for logical flaws.
- **Runtime Simulation**: Simulates code execution and potential outcomes.
- **Requirements Assessment**: Evaluates if the code meets specified requirements.
- **Code Quality Evaluation**: Assesses readability, organization, and adherence to best practices.
- **Point Deductions**: Calculates score reductions for various issues.
- **Extra Credit**: Considers exceptional work for additional points.
- **Overall Assessment**: Provides a summary and final score.

## Important Considerations for Usage

1. **Model Limitations**: The o1-preview model, while powerful, may not catch all nuances that a human grader would.
2. **Customization Needs**: Grading criteria and prompts may need adjustment for different assignments or courses.
3. **Feedback Review**: Regularly review AI-generated grades to ensure consistency and fairness.
4. **Edge Cases**: While error handling is implemented, unexpected scenarios may still occur.
5. **Performance**: Consider potential latency when grading multiple assignments, as each requires an API call.

## Batch Grading and Automation

While the Streamlit app provides an interactive interface, the grading functionality can be extended for batch processing:

1. **Batch Grading Script**: 
   - Create a Python script that iterates through a directory of Java files.
   - Use the `grade_assignment` function from `grader.py` for each file.
   - Store results in a structured format (e.g., JSON or CSV) for easy review.

2. **Learning Management System Integration**:
   - Utilize Selenium to automate browser interactions with your LMS.
   - Navigate through student submissions, download Java files, and trigger the grading process.
   - Upload grading results and feedback directly to the LMS.

3. **Enhanced Runtime Simulation**:
   - Implement a Java virtual environment within a sandbox.
   - Actually execute the student's code instead of relying solely on AI reasoning.
   - Capture runtime outputs, errors, and performance metrics for more accurate grading.

Example batch grading script structure:

```python
import os
from grader import grade_assignment

def batch_grade(directory, requirements_file):
    results = []
    with open(requirements_file, 'r') as f:
        guidelines = f.read()
    
    for filename in os.listdir(directory):
        if filename.endswith('.java'):
            with open(os.path.join(directory, filename), 'r') as f:
                java_code = f.read()
            result = grade_assignment(java_code, guidelines, "", 100, filename)
            results.append({"filename": filename, "grade": result})
    
    return results

# Usage
results = batch_grade("path/to/submissions", "path/to/requirements.txt")
```

## Future Improvements

1. **Language Expansion**: Extend support to other programming languages beyond Java.
2. **Actual Code Execution**: Implement a secure environment to run and test student code directly.
3. **Machine Learning Integration**: Train models on historical grading data to improve accuracy over time.
4. **Plagiarism Detection**: Incorporate algorithms to detect code similarity across submissions.
