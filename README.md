# CS 101 Assignment Grader

Automates the grading process for Java programming assignments. Utilizes the o1-preview model from OpenAI to conduct multi-step analysis of student code, with syntax checks, compilation tests, and a runtime simulation to detect logical errors + edge cases. Provides detailed feedback, and assigns scores based on criteria from assignment requirements. This system is designed specifically for CS 101 (Intro to Computer Science), taught in Java (so we must of course grade it using Python). :)

https://github.com/user-attachments/assets/363d3fba-7961-46ec-8ab3-e31a4a5e7aaf

## Key Features

1. **Automated Grading**: Analyzes Java code using the o1-preview model and provides a detailed assessment.
2. **Customizable Criteria**: Allows instructors to set specific grading requirements.
3. **Detailed Feedback**: Offers insights on syntax, logic, runtime behavior, and code quality.
4. **Flexible Scoring**: Supports variable maximum points and extra credit.
5. **Batch Processing**: CLI interface for efficient processing of multiple submissions.
6. **Brightspace Integration**: Tools for collecting and organizing submissions from Brightspace.

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

### 3. CLI Interface (`cli.py`)

The command-line interface provides efficient batch processing capabilities:

- **Submission Collection**: `collect-btsp` command for organizing Brightspace downloads:
  ```bash
  python cli.py collect-btsp dir1 dir2 output_dir
  ```

- **File Standardization**: `rename` command for normalizing submission filenames:
  ```bash
  python cli.py rename submissions_dir
  python cli.py rename submissions_dir --dry-run  # Preview changes
  ```

- **Batch Grading**: `grade` command for parallel processing of submissions:
  ```bash
  python cli.py grade submissions requirements.txt --threads 4 --max-points 150
  ```

### 4. Grading Process

1. **Input Collection**: 
   - Upload Java files (single or zip) containing student code
   - Provide assignment requirements as a text file
   - Optional student comments can be added
   - Set maximum points (default 100, range 10-200)

2. **AI Analysis**: The system sends the code, requirements, and grading criteria to the o1-preview model for analysis.

3. **Result Processing**: AI's response is parsed and structured into various assessment categories.

4. **Display**: 
   - Web UI: Interactive visualizations with gauge charts, pie charts, and detailed breakdowns
   - CLI: CSV output with comprehensive grading results for batch processing

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
5. **Performance**: 
   - Web UI: Consider latency for individual assignments due to API calls
   - CLI: Utilize parallel processing for efficient batch grading

## Future Improvements

1. **Language Expansion**: Extend support to other programming languages beyond Java.
2. **Actual Code Execution**: Implement a secure environment to run and test student code directly.
3. **Machine Learning Integration**: Train models on historical grading data to improve accuracy over time.
4. **Plagiarism Detection**: Incorporate algorithms to detect code similarity across submissions.
5. **LMS Integration**: Expand Brightspace integration to support other learning management systems.
